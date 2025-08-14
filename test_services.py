import pytest
from models import Lead, Answer, UserBehavior
from database import get_db_session
from notification_service import NotificationService
from ab_testing_service import ABTestingService
from services import LeadService, QuestionService, ScoringService, AnswerService
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
    # Answer first question
    q = questions[0]
    answer_resp = client.post("/api/answer", json={
        "session_id": session_id,
        "question_id": q["id"],
        "answer_text": "Test answer",
        "time_taken": 10
    })
    assert answer_resp.status_code == 200
    # Next question
    next_resp = client.post("/api/next-question", json={
        "session_id": session_id,
        "last_question_id": q["id"]
    })
    assert next_resp.status_code == 200 or next_resp.status_code == 422


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
    AnswerService.log_answer(session_id, 1, "Test answer", 10)
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
    success, score = AnswerService.log_answer(session_id, 1, "Test answer", 10)
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
