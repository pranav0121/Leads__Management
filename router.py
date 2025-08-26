from fastapi import Body
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from services import (QuestionService, AnswerService, ScoringService, LeadService,
                      CustomerService, PageTrackingService, CIFService, SessionExitService)
from notification_service import NotificationService
from ab_testing_service import ABTestingService
from config import Config
import uuid
import json

router = APIRouter()

# Define Pydantic models for requests


class SessionStartRequest(BaseModel):
    utm_source: str = "direct"


class LogAnswerRequest(BaseModel):
    session_id: str
    question_id: int
    answer_text: str
    time_taken: Optional[float] = None


class LogBehaviorRequest(BaseModel):
    session_id: str
    action: str
    metadata: Optional[dict] = None


class ProfileData(BaseModel):
    name: str
    email: str
    phone: str
    business_type: str
    location: str
    staff_size: str
    monthly_sales: str
    features_interested: list[str]


class LeadProfileRequest(BaseModel):
    session_id: str
    profile_data: dict = {
        "name": "string",
        "email": "string",
        "phone": "string",
        "business_type": "string",
        "location": "string",
        "staff_size": "string",
        "monthly_sales": "string",
        "features_interested": ["string"]
    }


class OdooSyncRequest(BaseModel):
    session_id: str


class ABTestVariantRequest(BaseModel):
    session_id: str


class ABTestConversionRequest(BaseModel):
    session_id: str
    test_name: str
    variant: str
    conversion_type: str
    conversion_value: Optional[float] = None


class LeadNotificationRequest(BaseModel):
    session_id: str


# Next Question Endpoint Model


class NextQuestionRequest(BaseModel):
    session_id: str
    last_question_id: int


# New: Customer ID Management Models
class CustomerIDRequest(BaseModel):
    session_id: str


# New: Customer Information Form Models
class CIFStartRequest(BaseModel):
    session_id: str
    customer_id: str


class CIFUpdateRequest(BaseModel):
    customer_id: str
    form_data: dict
    section: Optional[str] = None


# New: Session Exit Models
class SessionExitRequest(BaseModel):
    session_id: str
    exit_reason: str = "abandoned"
    exit_question_id: Optional[int] = None
    exit_page: Optional[str] = None
    last_action: Optional[str] = None
    metadata: Optional[dict] = None

# API Endpoints
# ...existing code...


@router.post("/api/next-question", tags=["Session & Question Flow"])
def get_next_question(request: NextQuestionRequest):
    """
    Returns the next unanswered question for the session after the given last_question_id.
    If all required questions are answered, returns None.
    """
    from database import get_db_session
    from models import Answer
    db_session = get_db_session()
    try:
        # Get all questions ordered
        questions = QuestionService.get_questions()
        questions_sorted = sorted(
            questions, key=lambda q: q.get('order_index', q['id']))

        # Get answered question IDs for this session
        answered = db_session.query(Answer.question_id).filter_by(
            session_id=request.session_id).distinct().all()
        answered_ids = set(row[0] for row in answered)

        # Find next unanswered required question after last_question_id
        found_last = False
        for q in questions_sorted:
            if not found_last:
                if q['id'] == request.last_question_id:
                    found_last = True
                continue
            if q.get('required', True) and q['id'] not in answered_ids:
                return q
        # If none left, return None
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_session.close()


@router.post("/api/session/start", tags=["Session & Question Flow"])
def start_session(request: SessionStartRequest):
    session_id = str(uuid.uuid4())
    success = LeadService.create_lead(session_id, request.utm_source)
    if success:
        return {"session_id": session_id, "message": "Session started successfully"}
    raise HTTPException(status_code=400, detail="Failed to start session")


@router.get("/api/questions", tags=["Session & Question Flow"])
def get_questions():
    questions = QuestionService.get_questions()
    return questions


@router.post("/api/answer", tags=["Session & Question Flow"])
def log_answer(request: LogAnswerRequest):
    if not all([request.session_id, request.question_id, request.answer_text]):
        raise HTTPException(status_code=400, detail="Missing required fields")
    success, score = AnswerService.log_answer(
        request.session_id, request.question_id, request.answer_text, request.time_taken)
    if success:
        return {"message": "Answer logged successfully", "score_earned": score}
    raise HTTPException(status_code=400, detail="Failed to log answer")


@router.post("/api/behavior", tags=["User Actions & Behaviors"])
def log_behavior(request: LogBehaviorRequest):
    if not all([request.session_id, request.action]):
        raise HTTPException(status_code=400, detail="Missing required fields")
    score_change = ScoringService.log_behavior(
        request.session_id, request.action, request.metadata)
    return {"message": "Behavior logged successfully", "score_change": score_change}


@router.get("/api/behavior/actions", tags=["User Actions & Behaviors"])
def get_valid_actions():
    """
    Returns all valid user actions that can be logged via /api/behavior.
    """
    from workflow_config import WORKFLOW_CONFIG
    scoring_map = WORKFLOW_CONFIG.get('scoring', {})
    actions = [action for action in scoring_map.keys()]
    return {"actions": actions}


@router.post("/api/lead/profile", tags=["Lead Profile & Data"])
def update_lead_profile(request: LeadProfileRequest):
    if not request.session_id:
        raise HTTPException(status_code=400, detail="Missing session_id")
    success = LeadService.update_lead_profile(
        request.session_id, request.profile_data)
    if success:
        return {"message": "Profile updated successfully"}
    raise HTTPException(status_code=400, detail="Failed to update profile")

    # Real-time sync to Odoo
    from services import OdooSyncService
    odoo_id = OdooSyncService.sync_lead(request.session_id)
    if odoo_id:
        return {"message": "Lead profile updated and synced to Odoo", "odoo_lead_id": odoo_id}
    else:
        return {"message": "Lead profile updated, but Odoo sync failed"}


@router.post("/api/lead/sync-odoo", tags=["CRM Integration"])
def sync_lead_to_odoo(request: OdooSyncRequest):
    from services import OdooSyncService
    odoo_id = OdooSyncService.sync_lead(request.session_id)
    if odoo_id:
        return {"message": "Lead synced to Odoo", "odoo_lead_id": odoo_id}
    raise HTTPException(status_code=500, detail="Odoo sync failed")


@router.get("/api/lead/summary/{session_id}", tags=["Lead Profile & Data"])
def get_lead_summary(session_id: str):
    summary = LeadService.get_lead_summary(session_id)
    if summary:
        return summary
    raise HTTPException(status_code=404, detail="Lead not found")


@router.get("/api/score/{session_id}", tags=["Scoring & Qualification"])
def get_current_score(session_id: str):
    summary = LeadService.get_lead_summary(session_id)
    if summary:
        return {
            'lead_score': summary['lead_score'],
            'lead_type': summary['lead_type']
        }
    raise HTTPException(status_code=404, detail="Lead not found")


@router.get("/api/product-menu", tags=["Product & CTA Options"])
def get_product_menu():
    from workflow_config import WORKFLOW_CONFIG
    return WORKFLOW_CONFIG['product_menu']


@router.get("/api/cta-options", tags=["Product & CTA Options"])
def get_cta_options():
    from workflow_config import WORKFLOW_CONFIG
    return WORKFLOW_CONFIG['cta_options']


@router.get("/api/lead/export/{session_id}", tags=["Lead Profile & Data"])
def export_lead_data(session_id: str):
    summary = LeadService.get_lead_summary(session_id)
    if summary:
        crm_data = {
            "name": summary.get('name', 'Unknown'),
            "location": summary.get('location', ''),
            "business_type": summary.get('business_type', ''),
            "staff_size": summary.get('staff_size', ''),
            "monthly_sales": summary.get('monthly_sales', ''),
            "features_interested": summary.get('features_interested', []),
            "contact_info": summary.get('phone', summary.get('email', '')),
            "email": summary.get('email', ''),
            "phone": summary.get('phone', ''),
            "lead_score": summary.get('lead_score', 0),
            "lead_type": summary.get('lead_type', 'Unqualified'),
            "utm_source": summary.get('utm_source', 'direct'),
            "session_start_time": summary.get('created_at', ''),
            "assigned_to": "CTL-Team"
        }
        return crm_data
    raise HTTPException(status_code=404, detail="Lead not found")


@router.get("/api/analytics/leads", tags=["Analytics & Reporting"])
def get_leads_analytics():
    try:
        from database import get_db_session
        from models import Lead, UserBehavior
        db_session = get_db_session()
        leads = db_session.query(Lead).all()
        total_leads = len(leads)
        sql_leads = len([l for l in leads if l.lead_type == 'SQL'])
        mql_leads = len([l for l in leads if l.lead_type == 'MQL'])
        unqualified_leads = len(
            [l for l in leads if l.lead_type == 'Unqualified'])
        average_score = sum([l.lead_score or 0 for l in leads]
                            ) / total_leads if total_leads else 0

        # Conversion rate: count of 'ab_test_conversion' actions
        conversions = db_session.query(UserBehavior).filter(
            UserBehavior.action == 'ab_test_conversion').count()
        conversion_rate = (conversions / total_leads *
                           100) if total_leads else 0

        # Completion rate: leads who answered all required questions
        completed = 0
        for lead in leads:
            from services import LeadService
            try:
                if LeadService.check_all_questions_answered(lead.session_id):
                    completed += 1
            except Exception as e:
                print(
                    f"Error checking questions for lead {lead.session_id}: {e}")
        completion_rate = (completed / total_leads * 100) if total_leads else 0

        analytics = {
            "total_leads": total_leads,
            "sql_leads": sql_leads,
            "mql_leads": mql_leads,
            "unqualified_leads": unqualified_leads,
            "conversion_rate": round(conversion_rate, 2),
            "average_score": round(average_score, 2),
            "completion_rate": round(completion_rate, 2)
        }
        db_session.close()
        return analytics
    except Exception as e:
        print(f"Error in analytics endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ...add other endpoints as needed...

# A/B Testing Endpoints


@router.post("/api/ab-test/variant", tags=["A/B Testing"])
def get_ab_test_variant(request: ABTestVariantRequest):
    variant = ABTestingService.get_variant(request.session_id)
    return {"variant": variant}


@router.post("/api/ab-test/conversion", tags=["A/B Testing"])
def log_ab_test_conversion(request: ABTestConversionRequest):
    success = ABTestingService.log_conversion(
        request.session_id, request.test_name, request.variant, request.conversion_type, request.conversion_value)
    if success:
        return {"message": "Conversion logged successfully"}
    raise HTTPException(status_code=400, detail="Failed to log conversion")

# Lead Notification Endpoint


@router.post("/api/lead/notify", tags=["Notifications"])
def notify_lead(request: LeadNotificationRequest):
    summary = LeadService.get_lead_summary(request.session_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Lead not found")
    success = NotificationService.notify_sales_team(summary)
    if success:
        return {"message": "Notification sent"}
    score = summary.get("lead_score", 0)
    threshold = 60
    raise HTTPException(
        status_code=400,
        detail=f"Notification not sent. Lead score is {score}. Must be >= {threshold} to send notification."
    )


# New: Customer ID Management Endpoints

@router.post("/api/customer/generate-id", tags=["Customer Management"])
def generate_customer_id(request: CustomerIDRequest):
    """Generate and assign a customer ID to a session"""
    customer_id = CustomerService.assign_customer_id(request.session_id)
    if customer_id:
        return {"customer_id": customer_id, "session_id": request.session_id}
    raise HTTPException(status_code=404, detail="Session not found")


@router.get("/api/customer/{customer_id}", tags=["Customer Management"])
def get_customer_details(customer_id: str):
    """Get complete customer details including journey and CIF data"""
    details = CustomerService.get_customer_details(customer_id)
    if details:
        return details
    raise HTTPException(status_code=404, detail="Customer not found")


# New: Page Tracking Endpoints (GET only for viewing journeys)


class PageEntryRequest(BaseModel):
    session_id: str
    page_identifier: str
    question_id: Optional[int] = None
    page_type: Optional[str] = None
    metadata: Optional[dict] = None


class PageExitRequest(BaseModel):
    page_tracking_id: int
    exit_time: Optional[str] = None


@router.post("/api/tracking/page-entry", tags=["Page Tracking"])
def log_page_entry(request: PageEntryRequest):
    page_tracking_id = PageTrackingService.log_page_entry(
        request.session_id,
        request.page_identifier,
        request.question_id,
        request.page_type,
        request.metadata
    )
    if page_tracking_id:
        return {"page_tracking_id": page_tracking_id}
    raise HTTPException(status_code=400, detail="Failed to log page entry")


@router.post("/api/tracking/page-exit", tags=["Page Tracking"])
def log_page_exit(request: PageExitRequest):
    success = PageTrackingService.log_page_exit(
        request.page_tracking_id,
        None  # Optionally parse exit_time if provided
    )
    if success:
        return {"success": True}
    raise HTTPException(status_code=400, detail="Failed to log page exit")


@router.get("/api/tracking/journey/{session_id}", tags=["Page Tracking"])
def get_customer_journey(session_id: str):
    """Get complete page journey for a session"""
    journey = PageTrackingService.get_customer_journey(session_id)
    return {"session_id": session_id, "journey": journey}


@router.get("/api/tracking/customer-journey/{customer_id}", tags=["Page Tracking"])
def get_customer_journey_by_id(customer_id: str):
    """Get complete page journey for a customer by customer ID"""
    # First get the customer details to find session_id
    customer_details = CustomerService.get_customer_details(customer_id)
    if not customer_details:
        raise HTTPException(status_code=404, detail="Customer not found")

    session_id = customer_details["session_id"]
    journey = PageTrackingService.get_customer_journey(session_id)

    return {
        "customer_id": customer_id,
        "session_id": session_id,
        "journey": journey,
        "summary": {
            "total_pages_visited": len(journey),
            "total_time_spent": sum(page.get("time_spent", 0) or 0 for page in journey),
            "completion_status": "completed" if any(page.get("page_type") == "completion" for page in journey) else "in_progress"
        }
    }


@router.get("/api/tracking/visual-journey/{identifier}", tags=["Page Tracking"])
def get_visual_journey(identifier: str, id_type: str = "session"):
    """Get visual representation of customer journey (session_id or customer_id)"""
    try:
        if id_type == "customer":
            # Get by customer ID
            customer_details = CustomerService.get_customer_details(identifier)
            if not customer_details:
                raise HTTPException(
                    status_code=404, detail="Customer not found")
            session_id = customer_details["session_id"]
            journey = customer_details["page_journey"]
        else:
            # Get by session ID
            session_id = identifier
            journey = PageTrackingService.get_customer_journey(session_id)

        # Create visual journey representation
        visual_journey = []
        for i, page in enumerate(journey):
            visual_page = {
                "step": i + 1,
                "page_name": page.get("page", "Unknown"),
                "question_id": page.get("question_id"),
                "entry_time": page.get("entry_time"),
                "exit_time": page.get("exit_time"),
                "time_spent_seconds": page.get("time_spent", 0),
                "time_spent_formatted": f"{page.get('time_spent', 0) or 0}s",
                "page_type": page.get("page_type", "unknown"),
                "status": "completed" if page.get("exit_time") else "current"
            }
            visual_journey.append(visual_page)

        # Calculate journey statistics
        total_time = sum(page.get("time_spent", 0) or 0 for page in journey)
        avg_time_per_page = total_time / len(journey) if journey else 0

        return {
            "identifier": identifier,
            "id_type": id_type,
            "session_id": session_id,
            "visual_journey": visual_journey,
            "statistics": {
                "total_pages": len(journey),
                "total_time_seconds": total_time,
                "total_time_formatted": f"{total_time // 60}m {total_time % 60}s",
                "average_time_per_page": f"{avg_time_per_page:.1f}s",
                "completion_rate": f"{(len([p for p in journey if p.get('exit_time')]) / len(journey) * 100):.1f}%" if journey else "0%"
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error retrieving journey: {str(e)}")


# New: Customer Information Form (CIF) Endpoints

@router.post("/api/cif/start", tags=["Customer Information Form"])
def start_cif(request: CIFStartRequest):
    """Start CIF process for a customer"""
    cif_id = CIFService.start_cif(request.session_id, request.customer_id)
    if cif_id:
        return {"message": "CIF started", "cif_id": cif_id, "customer_id": request.customer_id}
    raise HTTPException(status_code=400, detail="Failed to start CIF")


@router.put("/api/cif/update", tags=["Customer Information Form"])
def update_cif(request: CIFUpdateRequest):
    """Update CIF data for a customer"""
    success = CIFService.update_cif_data(
        request.customer_id,
        request.form_data,
        request.section
    )
    if success:
        return {"message": "CIF updated successfully", "customer_id": request.customer_id}
    raise HTTPException(status_code=400, detail="Failed to update CIF")


@router.post("/api/cif/complete", tags=["Customer Information Form"])
def complete_cif(request: CIFUpdateRequest):
    """Mark CIF as completed and update final data"""
    success = CIFService.update_cif_data(
        request.customer_id, request.form_data)
    if success:
        return {"message": "CIF completed successfully", "customer_id": request.customer_id}
    raise HTTPException(status_code=400, detail="Failed to complete CIF")


@router.get("/api/cif/{customer_id}", tags=["Customer Information Form"])
def get_cif_data(customer_id: str):
    """Get CIF data for a customer"""
    cif_data = CIFService.get_cif_data(customer_id)
    if cif_data:
        return cif_data
    raise HTTPException(status_code=404, detail="CIF data not found")


# New: Session Exit Tracking Endpoints

@router.post("/api/session/exit", tags=["Session Management"])
def log_session_exit(request: SessionExitRequest):
    """Log session exit/abandonment"""
    exit_id = SessionExitService.log_session_exit(
        request.session_id,
        request.exit_reason,
        request.exit_question_id,
        request.exit_page,
        request.last_action,
        request.metadata
    )
    if exit_id:
        return {"message": "Session exit logged", "exit_id": exit_id}
    raise HTTPException(status_code=400, detail="Failed to log session exit")


# New: Advanced Analytics Endpoints

@router.get("/api/analytics/drop-off-points", tags=["Advanced Analytics"])
def get_drop_off_analytics():
    """Get analytics on where users typically abandon sessions"""
    analytics = SessionExitService.get_abandonment_analytics()
    return analytics


@router.get("/api/analytics/page-performance", tags=["Advanced Analytics"])
def get_page_performance():
    """Get page-wise engagement metrics"""
    from services import PageTrackingService
    # Example: Aggregate page views, avg time, conversion rates
    analytics = PageTrackingService.get_page_performance_analytics()
    return analytics


@router.get("/api/analytics/customer-journey", tags=["Advanced Analytics"])
def get_journey_analytics():
    """Get journey analysis across all customers"""
    from services import PageTrackingService
    # Example: Aggregate journeys for all customers
    analytics = PageTrackingService.get_all_customer_journeys()
    return analytics


@router.get("/api/analytics/cif-completion", tags=["Advanced Analytics"])
def get_cif_completion_analytics():
    """Get CIF completion rates and analytics"""
    from services import CIFService
    # Example: Aggregate CIF completion rates and breakdowns
    analytics = CIFService.get_cif_completion_analytics()
    return analytics
