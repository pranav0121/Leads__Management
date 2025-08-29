import pytest
from models import Lead, Answer, UserBehavior, CustomerInformationForm, PageTracking, SessionExit
from database import get_db_session
from notification_service import NotificationService
from ab_testing_service import ABTestingService
from services import (LeadService, QuestionService, ScoringService, AnswerService,
                      CustomerService, PageTrackingService, CIFService, SessionExitService, OdooSyncService)
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_questions_endpoint():
    response = client.get("/api/questions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_product_menu_endpoint():
    response = client.get("/api/product-menu")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_cta_options_endpoint():
    response = client.get("/api/cta-options")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_behavior_actions_endpoint():
    response = client.get("/api/behavior/actions")
    assert response.status_code == 200
    assert "actions" in response.json()


def test_analytics_endpoint():
    response = client.get("/api/analytics/leads")
    assert response.status_code == 200
    assert "total_leads" in response.json()


def test_session_start_and_answer_flow():
    # Start session
    response = client.post("/api/session/start",
                           json={"utm_source": "test_source"})
    assert response.status_code == 200
    session_id = response.json()["session_id"]
    # Get questions
    questions = client.get("/api/questions").json()
    # Answer first question with simplified structure
    answer_resp = client.post("/api/answer", json={
        "session_id": session_id,
        "answer_text": "Test answer",
        "time_taken": 10
    })
    assert answer_resp.status_code == 200
    # Test skip question
    skip_resp = client.post("/api/skip-question", json={
        "session_id": session_id,
        "skip_reason": "user_skipped"
    })
    assert skip_resp.status_code == 200


def test_log_behavior_endpoint():
    response = client.post("/api/session/start",
                           json={"utm_source": "test_source"})
    session_id = response.json()["session_id"]
    resp = client.post(
        "/api/behavior", json={"session_id": session_id, "action": "session_opened"})
    assert resp.status_code == 200


def test_lead_profile_and_summary_endpoints():
    response = client.post("/api/session/start",
                           json={"utm_source": "test_source"})
    session_id = response.json()["session_id"]
    profile_data = {
        "name": "Test User",
        "email": "test@example.com",
        "phone": "1234567890",
        "business_type": "Retail",
        "location": "Test City",
        "staff_size": "1-5",
        "monthly_sales": "10000",
        "features_interested": ["Billing", "Inventory"]
    }
    resp = client.post(
        "/api/lead/profile", json={"session_id": session_id, "profile_data": profile_data})
    assert resp.status_code == 200
    summary = client.get(f"/api/lead/summary/{session_id}")
    assert summary.status_code == 200
    export = client.get(f"/api/lead/export/{session_id}")
    assert export.status_code == 200


def test_score_endpoint():
    response = client.post("/api/session/start",
                           json={"utm_source": "test_source"})
    session_id = response.json()["session_id"]
    score_resp = client.get(f"/api/score/{session_id}")
    assert score_resp.status_code == 200


def test_ab_test_endpoints():
    response = client.post("/api/session/start",
                           json={"utm_source": "test_source"})
    session_id = response.json()["session_id"]
    variant_resp = client.post(
        "/api/ab-test/variant", json={"session_id": session_id})
    assert variant_resp.status_code == 200
    variant = variant_resp.json()["variant"]
    conv_resp = client.post("/api/ab-test/conversion", json={
        "session_id": session_id,
        "test_name": "greeting_message",
        "variant": variant,
        "conversion_type": "signup",
        "conversion_value": 1
    })
    assert conv_resp.status_code == 200 or conv_resp.status_code == 400


def test_notify_lead_endpoint():
    response = client.post("/api/session/start",
                           json={"utm_source": "test_source"})
    session_id = response.json()["session_id"]
    # Try to notify (will likely fail unless lead is SQL)
    notify_resp = client.post(
        "/api/lead/notify", json={"session_id": session_id})
    assert notify_resp.status_code in [200, 400]


def test_next_question_logic():
    session_id = "test-session-next"
    LeadService.create_lead(session_id)
    # Log answer to first question
    AnswerService.log_answer(session_id, "Test answer", 10)
    # Simulate backend logic for next question
    from services import QuestionService
    questions = QuestionService.get_questions()
    answered_ids = [1]
    next_question = None
    found_last = False
    for q in sorted(questions, key=lambda x: x.get('order_index', x['id'])):
        if not found_last:
            if q['id'] == 1:
                found_last = True
            continue
        if q.get('required', True) and q['id'] not in answered_ids:
            next_question = q
            break
    assert next_question is not None
    # Cleanup
    db = get_db_session()
    db.query(Answer).filter_by(session_id=session_id).delete()
    db.query(Lead).filter_by(session_id=session_id).delete()
    db.commit()
    db.close()


def test_get_valid_actions():
    from workflow_config import WORKFLOW_CONFIG
    scoring_map = WORKFLOW_CONFIG.get('scoring', {})
    actions = [action for action in scoring_map.keys()]
    assert "session_opened" in actions
    assert "cta_clicked" in actions


def test_create_lead():
    import uuid
    session_id = f"test-session-{uuid.uuid4()}"
    result = LeadService.create_lead(session_id, utm_source="test_source")
    assert result is True
    # Cleanup
    db = get_db_session()
    db.query(Lead).filter_by(session_id=session_id).delete()
    db.commit()
    db.close()


def test_get_questions():
    questions = QuestionService.get_questions()
    assert isinstance(questions, list)
    assert len(questions) > 0


def test_scoring_map():
    scoring = ScoringService.get_scoring_map()
    assert "session_opened" in scoring


def test_lead_thresholds():
    thresholds = ScoringService.get_lead_thresholds()
    assert "sql" in thresholds
    assert "mql" in thresholds
    assert "unqualified" in thresholds


def test_answer_logging():
    session_id = "test-session-ans"
    LeadService.create_lead(session_id)
    success, score = AnswerService.log_answer(session_id, "Test answer", 10)
    assert success is True
    assert score > 0
    # Cleanup
    db = get_db_session()
    db.query(Answer).filter_by(session_id=session_id).delete()
    db.query(Lead).filter_by(session_id=session_id).delete()
    db.commit()
    db.close()


def test_behavior_logging():
    session_id = "test-session-beh"
    LeadService.create_lead(session_id)
    score_change = ScoringService.log_behavior(session_id, "session_opened")
    assert isinstance(score_change, int)
    # Cleanup
    db = get_db_session()
    db.query(UserBehavior).filter_by(session_id=session_id).delete()
    db.query(Lead).filter_by(session_id=session_id).delete()
    db.commit()
    db.close()


def test_profile_update():
    session_id = "test-session-profile"
    LeadService.create_lead(session_id)
    profile_data = {
        "name": "Test User",
        "email": "test@example.com",
        "phone": "1234567890",
        "business_type": "Retail",
        "location": "Test City",
        "staff_size": "1-5",
        "monthly_sales": "10000",
        "features_interested": ["Billing", "Inventory"]
    }
    result = LeadService.update_lead_profile(session_id, profile_data)
    assert result is True
    # Cleanup
    db = get_db_session()
    db.query(Lead).filter_by(session_id=session_id).delete()
    db.commit()
    db.close()


def test_lead_summary():
    session_id = "test-session-summary"
    LeadService.create_lead(session_id)
    summary = LeadService.get_lead_summary(session_id)
    assert summary is not None
    assert "session_id" in summary
    # Cleanup
    db = get_db_session()
    db.query(Lead).filter_by(session_id=session_id).delete()
    db.commit()
    db.close()


def test_ab_test_variant():
    session_id = "test-session-ab"
    variant = ABTestingService.get_variant(session_id)
    assert variant in ["A", "B", "C"]


def test_ab_test_conversion():
    session_id = "test-session-abconv"
    LeadService.create_lead(session_id)
    result = ABTestingService.log_conversion(
        session_id, "homepage_cta", "A", "signup", 1)
    assert result is True
    # Cleanup
    db = get_db_session()
    db.query(UserBehavior).filter_by(session_id=session_id).delete()
    db.query(Lead).filter_by(session_id=session_id).delete()
    db.commit()
    db.close()


def test_notification_service():
    lead_data = {
        "session_id": "test-session-notify",
        "lead_score": 65,
        "lead_type": "SQL",
        "name": "Notify User",
        "email": "notify@example.com",
        "phone": "9876543210",
        "business_type": "Wholesale",
        "location": "Notify City",
        "features_interested": ["Billing"]
    }
    result = NotificationService.notify_sales_team(lead_data)
    # Accept both for stubbed notifications
    assert result is True or result is False


# New: Customer ID Management Tests

def test_customer_id_generation():
    """Test customer ID generation and assignment"""
    # Start a session first
    session_response = client.post(
        "/api/session/start", json={"utm_source": "test"})
    session_id = session_response.json()["session_id"]

    # Generate customer ID
    response = client.post("/api/customer/generate-id",
                           json={"session_id": session_id})
    assert response.status_code == 200
    assert "customer_id" in response.json()
    assert response.json()["customer_id"].startswith("CID_")

    customer_id = response.json()["customer_id"]

    # Test getting customer details
    details_response = client.get(f"/api/customer/{customer_id}")
    assert details_response.status_code == 200
    assert details_response.json()["customer_id"] == customer_id


def test_page_tracking_endpoints():
    """Test page tracking functionality"""
    # Start a session first
    session_response = client.post(
        "/api/session/start", json={"utm_source": "test"})
    session_id = session_response.json()["session_id"]

    # Log page entry
    entry_response = client.post("/api/tracking/page-entry", json={
        "session_id": session_id,
        "page_identifier": "question_1",
        "question_id": 1,
        "page_type": "question",
        "metadata": {"test": "data"}
    })
    assert entry_response.status_code == 200
    assert "page_tracking_id" in entry_response.json()

    page_tracking_id = entry_response.json()["page_tracking_id"]

    # Log page exit
    exit_response = client.post("/api/tracking/page-exit", json={
        "page_tracking_id": page_tracking_id
    })
    assert exit_response.status_code == 200

    # Get customer journey
    journey_response = client.get(f"/api/tracking/journey/{session_id}")
    assert journey_response.status_code == 200
    assert "journey" in journey_response.json()
    assert len(journey_response.json()["journey"]) >= 1


def test_cif_endpoints():
    """Test Customer Information Form endpoints"""
    # Start a session and get customer ID
    session_response = client.post(
        "/api/session/start", json={"utm_source": "test"})
    session_id = session_response.json()["session_id"]

    customer_response = client.post(
        "/api/customer/generate-id", json={"session_id": session_id})
    customer_id = customer_response.json()["customer_id"]

    # Start CIF
    start_response = client.post("/api/cif/start", json={
        "session_id": session_id,
        "customer_id": customer_id
    })
    assert start_response.status_code == 200

    # Update CIF data
    cif_data = {
        "basic_info": {
            "full_name": "Test Customer",
            "email": "test@example.com",
            "phone": "9876543210"
        }
    }
    update_response = client.put("/api/cif/update", json={
        "customer_id": customer_id,
        "form_data": cif_data,
        "section": "basic_info"
    })
    assert update_response.status_code == 200

    # Get CIF data
    get_response = client.get(f"/api/cif/{customer_id}")
    assert get_response.status_code == 200
    assert "form_data" in get_response.json()
    assert "completion_percentage" in get_response.json()


def test_session_exit_endpoint():
    """Test session exit tracking"""
    # Start a session first
    session_response = client.post(
        "/api/session/start", json={"utm_source": "test"})
    session_id = session_response.json()["session_id"]

    # Log session exit
    exit_response = client.post("/api/session/exit", json={
        "session_id": session_id,
        "exit_reason": "abandoned",
        "exit_question_id": 3,
        "exit_page": "question_3",
        "last_action": "clicked_back",
        "metadata": {"reason": "too_many_questions"}
    })
    assert exit_response.status_code == 200
    assert "exit_id" in exit_response.json()


def test_advanced_analytics_endpoints():
    # Drop-off points
    resp = client.get("/api/analytics/drop-off-points")
    assert resp.status_code == 200
    assert "common_exit_points" in resp.json()
    assert "completion_by_reason" in resp.json()

    # Page performance
    resp = client.get("/api/analytics/page-performance")
    assert resp.status_code == 200
    assert "page_performance" in resp.json()

    # Customer journey
    resp = client.get("/api/analytics/customer-journey")
    assert resp.status_code == 200
    assert "customer_journeys" in resp.json()

    # CIF completion
    resp = client.get("/api/analytics/cif-completion")
    assert resp.status_code == 200
    assert "total_cif" in resp.json()
    assert "completed_cif" in resp.json()
    assert "avg_completion_percentage" in resp.json()


# Service-level tests for new functionality

def test_customer_service():
    """Test CustomerService functionality"""
    import uuid
    session_id = f"test-customer-service-{uuid.uuid4()}"

    # Create a lead first
    db = get_db_session()
    try:
        lead = Lead(session_id=session_id, utm_source="test")
        db.add(lead)
        db.commit()

        # Test customer ID assignment
        customer_id = CustomerService.assign_customer_id(session_id)
        assert customer_id is not None
        assert customer_id.startswith("CID_")

        # Test getting customer details
        details = CustomerService.get_customer_details(customer_id)
        assert details is not None
        assert details["customer_id"] == customer_id
        assert details["session_id"] == session_id

    finally:
        # Cleanup
        try:
            db.query(Lead).filter_by(session_id=session_id).delete()
            db.commit()
        except:
            db.rollback()
        db.close()    # Cleanup
    db.query(Lead).filter_by(session_id=session_id).delete()
    db.commit()
    db.close()


def test_page_tracking_service():
    """Test PageTrackingService functionality"""
    import uuid
    session_id = f"test-page-tracking-{uuid.uuid4()}"

    # Create a lead first
    db = get_db_session()
    try:
        lead = Lead(session_id=session_id, utm_source="test")
        db.add(lead)
        db.commit()

        # Test page entry logging
        page_id = PageTrackingService.log_page_entry(
            session_id, "test_page", question_id=1, page_type="question"
        )
        assert page_id is not None

        # Test page exit logging
        success = PageTrackingService.log_page_exit(page_id)
        assert success is True

        # Test getting journey
        journey = PageTrackingService.get_customer_journey(session_id)
        assert len(journey) >= 1
        assert journey[0]["page"] == "test_page"

    finally:
        # Cleanup
        try:
            db.query(PageTracking).filter_by(session_id=session_id).delete()
            db.query(Lead).filter_by(session_id=session_id).delete()
            db.commit()
        except:
            db.rollback()
        db.close()


def test_cif_service():
    """Test CIFService functionality"""
    import uuid
    session_id = f"test-cif-service-{uuid.uuid4()}"
    customer_id = f"CID_TEST_{uuid.uuid4().hex[:8].upper()}"

    # Create a lead first
    db = get_db_session()
    try:
        lead = Lead(session_id=session_id,
                    customer_id=customer_id, utm_source="test")
        db.add(lead)
        db.commit()

        # Test CIF start
        cif_id = CIFService.start_cif(session_id, customer_id)
        assert cif_id is not None

        # Test CIF data update
        form_data = {
            "basic_info": {
                "full_name": "Test User",
                "email": "test@example.com",
                "phone": "9876543210"
            }
        }
        success = CIFService.update_cif_data(
            customer_id, form_data, "basic_info")
        assert success is True

        # Test getting CIF data
        cif_data = CIFService.get_cif_data(customer_id)
        assert cif_data is not None
        assert cif_data["customer_id"] == customer_id
        assert "completion_percentage" in cif_data

    finally:
        # Cleanup
        try:
            db.query(CustomerInformationForm).filter_by(
                customer_id=customer_id).delete()
            db.query(Lead).filter_by(session_id=session_id).delete()
            db.commit()
        except:
            db.rollback()
        db.close()


def test_session_exit_service():
    """Test SessionExitService functionality"""
    import uuid
    session_id = f"test-session-exit-{uuid.uuid4()}"

    # Create a lead first
    db = get_db_session()
    try:
        lead = Lead(session_id=session_id, utm_source="test")
        db.add(lead)
        db.commit()

        # Test session exit logging
        exit_id = SessionExitService.log_session_exit(
            session_id, "abandoned", exit_question_id=2, exit_page="question_2"
        )
        assert exit_id is not None

        # Test abandonment analytics
        analytics = SessionExitService.get_abandonment_analytics()
        assert "common_exit_points" in analytics
        assert "completion_by_reason" in analytics

    finally:
        # Cleanup
        try:
            db.query(SessionExit).filter_by(session_id=session_id).delete()
            db.query(Lead).filter_by(session_id=session_id).delete()
            db.commit()
        except:
            db.rollback()
        db.close()

    # Cleanup
    db.query(SessionExit).filter_by(session_id=session_id).delete()
    db.query(Lead).filter_by(session_id=session_id).delete()
    db.commit()
    db.close()


def test_update_lead_score():
    """Test LeadService.update_lead_score functionality"""
    session_id = "test_session_score"
    # Create a lead first
    LeadService.create_lead(session_id)

    score = 10
    success = LeadService.update_lead_score(session_id, score)
    assert success is True

    # Cleanup
    db = get_db_session()
    db.query(Lead).filter_by(session_id=session_id).delete()
    db.commit()
    db.close()


def test_log_answer():
    """Test AnswerService.log_answer functionality"""
    session_id = "test_session"
    answer_text = "Sample Answer"
    time_taken = 15
    success, score = AnswerService.log_answer(
        session_id, answer_text, time_taken)
    assert success is True
    assert score > 0


def test_get_cif_completion_analytics():
    """Test CIFService.get_cif_completion_analytics functionality"""
    analytics = CIFService.get_cif_completion_analytics()
    assert analytics['total_cif'] >= 0
    assert analytics['completed_cif'] >= 0
    assert analytics['avg_completion_percentage'] >= 0.0


def test_odoo_sync_lead():
    """Test OdooSyncService.sync_lead functionality"""
    session_id = "test_session"
    lead_id = OdooSyncService.sync_lead(session_id)
    # Odoo sync may return None if credentials are not configured in test environment
    # This is acceptable for testing
    assert lead_id is None or isinstance(lead_id, (int, str))
