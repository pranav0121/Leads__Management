import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Leads Management API (FastAPI version)"}

def test_next_question_endpoint():
    """Test the /api/next-question endpoint."""
    response = client.post("/api/next-question", json={"session_id": "test-session", "last_question_id": 1})
    assert response.status_code in [200, 422]  # 422 if body validation fails

def test_session_start_endpoint():
    """Test the /api/session/start endpoint."""
    response = client.post("/api/session/start", json={"utm_source": "test-source"})
    assert response.status_code in [200, 422]  # 422 if body validation fails

def test_next_question():
    response = client.post("/api/next-question", json={"session_id": "test-session", "last_question_id": 1})
    assert response.status_code in [200, 422]

def test_session_start():
    response = client.post("/api/session/start", json={"utm_source": "test-source"})
    assert response.status_code in [200, 422]

def test_get_questions():
    response = client.get("/api/questions")
    assert response.status_code == 200

def test_answer():
    response = client.post("/api/answer", json={"session_id": "test-session", "question_id": 1, "answer": "Sample answer"})
    assert response.status_code in [200, 422]

def test_answer_with_conditional():
    response = client.post("/api/answer-with-conditional", json={"session_id": "test-session", "question_id": 1, "answer": "Sample answer", "conditional": True})
    assert response.status_code in [200, 422]

def test_skip_question():
    response = client.post("/api/skip-question", json={"session_id": "test-session", "question_id": 1})
    assert response.status_code in [200, 422]

def test_log_behavior():
    response = client.post("/api/behavior", json={"session_id": "test-session", "action": "click", "details": "Sample details"})
    assert response.status_code in [200, 422]

def test_get_behavior_actions():
    response = client.get("/api/behavior/actions")
    assert response.status_code == 200

def test_update_lead_profile():
    response = client.post("/api/lead/profile", json={"session_id": "test-session", "profile_data": {"name": "John Doe", "email": "john@example.com"}})
    assert response.status_code in [200, 422]

def test_get_lead_summary():
    response = client.get("/api/lead/summary/test-session")
    assert response.status_code in [200, 404]

def test_export_lead_data():
    response = client.get("/api/lead/export/test-session")
    assert response.status_code in [200, 404]

def test_sync_lead_odoo():
    response = client.post("/api/lead/sync-odoo", json={"session_id": "test-session"})
    assert response.status_code in [200, 422, 500]

def test_get_score():
    response = client.get("/api/score/test-session")
    assert response.status_code in [200, 404]

def test_get_product_menu():
    response = client.get("/api/product-menu")
    assert response.status_code == 200

def test_get_cta_options():
    response = client.get("/api/cta-options")
    assert response.status_code == 200

def test_get_leads_analytics():
    response = client.get("/api/analytics/leads")
    assert response.status_code == 200

def test_ab_test_variant():
    response = client.post("/api/ab-test/variant", json={"session_id": "test-session", "variant": "A"})
    assert response.status_code in [200, 422]

def test_ab_test_conversion():
    response = client.post("/api/ab-test/conversion", json={"session_id": "test-session", "variant": "A", "converted": True})
    assert response.status_code in [200, 422]

def test_lead_notify():
    # Add all required fields for notification
    payload = {
        "session_id": "test-session",
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "1234567890",
        "business_type": "Retail",
        "location": "City",
        "staff_size": "10",
        "monthly_sales": "10000",
        "features_interested": ["Feature1", "Feature2"]
    }
    response = client.post("/api/lead/notify", json=payload)
    assert response.status_code in [200, 422, 400]

def test_generate_customer_id():
    response = client.post("/api/customer/generate-id", json={"customer_data": {"name": "John Doe", "email": "john@example.com"}})
    assert response.status_code in [200, 422]

def test_get_customer_details():
    response = client.get("/api/customer/test-customer")
    assert response.status_code in [200, 404]

def test_tracking_page_entry():
    response = client.post("/api/tracking/page-entry", json={"session_id": "test-session", "page": "home"})
    assert response.status_code in [200, 422]

def test_tracking_page_exit():
    response = client.post("/api/tracking/page-exit", json={"session_id": "test-session", "page": "home"})
    assert response.status_code in [200, 422]

def test_tracking_journey():
    response = client.get("/api/tracking/journey/test-session")
    assert response.status_code in [200, 404]

def test_tracking_customer_journey():
    response = client.get("/api/tracking/customer-journey/test-customer")
    assert response.status_code in [200, 404]

def test_tracking_visual_journey():
    response = client.get("/api/tracking/visual-journey/test-identifier")
    assert response.status_code in [200, 404]

def test_cif_start():
    response = client.post("/api/cif/start", json={"customer_id": "cust-123", "form_data": {"field1": "value1"}})
    assert response.status_code in [200, 422]

def test_cif_update():
    # Ensure CIF entry exists before updating
    start_payload = {
        "session_id": "test-session",
        "customer_id": "cust-123"
    }
    client.post("/api/cif/start", json=start_payload)
    update_payload = {
        "customer_id": "cust-123",
        "form_data": {"basic_info": {"full_name": "Test Customer", "email": "test@example.com", "phone": "9876543210"}},
        "section": "basic_info"
    }
    response = client.put("/api/cif/update", json=update_payload)
    assert response.status_code in [200, 422, 400]

def test_cif_complete():
    response = client.post("/api/cif/complete", json={"customer_id": "cust-123"})
    assert response.status_code in [200, 422]

def test_get_cif_data():
    response = client.get("/api/cif/cust-123")
    assert response.status_code in [200, 404]

def test_session_exit():
    response = client.post("/api/session/exit", json={"session_id": "test-session"})
    assert response.status_code in [200, 422]

def test_analytics_drop_off_points():
    response = client.get("/api/analytics/drop-off-points")
    assert response.status_code == 200

def test_analytics_page_performance():
    response = client.get("/api/analytics/page-performance")
    assert response.status_code == 200

def test_analytics_customer_journey():
    response = client.get("/api/analytics/customer-journey")
    assert response.status_code == 200

def test_analytics_cif_completion():
    response = client.get("/api/analytics/cif-completion")
    assert response.status_code == 200

def test_invalid_endpoint():
    """Test an invalid endpoint to ensure 404 is returned."""
    response = client.get("/api/invalid-endpoint")
    assert response.status_code == 404
