from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from services import QuestionService, AnswerService, ScoringService, LeadService
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
    profile_data: ProfileData


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
        request.session_id, request.profile_data.model_dump())
    if success:
        return {"message": "Profile updated successfully"}
    raise HTTPException(status_code=400, detail="Failed to update profile")


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
            if LeadService.check_all_questions_answered(lead.session_id):
                completed += 1
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
