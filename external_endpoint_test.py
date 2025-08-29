import requests

BASE_URL = "http://127.0.0.1:8000"

def test_root():
    r = requests.get(f"{BASE_URL}/")
    print("GET /", r.status_code, r.text)

def test_next_question():
    payload = {"session_id": "test-session", "last_question_id": 1}
    r = requests.post(f"{BASE_URL}/api/next-question", json=payload)
    print("POST /api/next-question", r.status_code, r.text)

def test_session_start():
    payload = {"utm_source": "test-source"}
    r = requests.post(f"{BASE_URL}/api/session/start", json=payload)
    print("POST /api/session/start", r.status_code, r.text)

def test_get_questions():
    r = requests.get(f"{BASE_URL}/api/questions")
    print("GET /api/questions", r.status_code, r.text)

def test_answer():
    payload = {"session_id": "test-session", "question_id": 1, "answer_text": "Sample answer"}
    r = requests.post(f"{BASE_URL}/api/answer", json=payload)
    print("POST /api/answer", r.status_code, r.text)

def test_answer_with_conditional():
    payload = {"session_id": "test-session", "question_id": 1, "answer_text": "Sample answer", "conditional": True}
    r = requests.post(f"{BASE_URL}/api/answer-with-conditional", json=payload)
    print("POST /api/answer-with-conditional", r.status_code, r.text)

def test_skip_question():
    payload = {"session_id": "test-session", "question_id": 1}
    r = requests.post(f"{BASE_URL}/api/skip-question", json=payload)
    print("POST /api/skip-question", r.status_code, r.text)

def test_log_behavior():
    payload = {"session_id": "test-session", "action": "click", "details": "Sample details"}
    r = requests.post(f"{BASE_URL}/api/behavior", json=payload)
    print("POST /api/behavior", r.status_code, r.text)

def test_get_behavior_actions():
    r = requests.get(f"{BASE_URL}/api/behavior/actions")
    print("GET /api/behavior/actions", r.status_code, r.text)

def test_update_lead_profile():
    payload = {"session_id": "test-session", "profile_data": {"name": "John Doe", "email": "john@example.com"}}
    r = requests.post(f"{BASE_URL}/api/lead/profile", json=payload)
    print("POST /api/lead/profile", r.status_code, r.text)

def test_update_lead_profile_high_score():
    # Update lead profile with high-value data
    payload = {
        "session_id": "test-session",
        "profile_data": {
            "name": "High Value Lead",
            "email": "highvalue@example.com",
            "phone": "9999999999",
            "business_type": "Retail",
            "location": "City",
            "staff_size": "More than 15",
            "monthly_sales": "₹5L+",
            "features_interested": ["Billing / Invoicing", "Loans"]
        }
    }
    r = requests.post(f"{BASE_URL}/api/lead/profile", json=payload)
    print("POST /api/lead/profile (high score)", r.status_code, r.text)

def test_get_lead_summary():
    r = requests.get(f"{BASE_URL}/api/lead/summary/test-session")
    print("GET /api/lead/summary/test-session", r.status_code, r.text)

def test_export_lead_data():
    r = requests.get(f"{BASE_URL}/api/lead/export/test-session")
    print("GET /api/lead/export/test-session", r.status_code, r.text)

def test_sync_lead_odoo():
    payload = {"session_id": "test-session"}
    r = requests.post(f"{BASE_URL}/api/lead/sync-odoo", json=payload)
    print("POST /api/lead/sync-odoo", r.status_code, r.text)

def test_get_score():
    r = requests.get(f"{BASE_URL}/api/score/test-session")
    print("GET /api/score/test-session", r.status_code, r.text)

def test_get_product_menu():
    r = requests.get(f"{BASE_URL}/api/product-menu")
    print("GET /api/product-menu", r.status_code, r.text)

def test_get_cta_options():
    r = requests.get(f"{BASE_URL}/api/cta-options")
    print("GET /api/cta-options", r.status_code, r.text)

def test_get_leads_analytics():
    r = requests.get(f"{BASE_URL}/api/analytics/leads")
    print("GET /api/analytics/leads", r.status_code, r.text)

def test_ab_test_variant():
    payload = {"session_id": "test-session", "variant": "A"}
    r = requests.post(f"{BASE_URL}/api/ab-test/variant", json=payload)
    print("POST /api/ab-test/variant", r.status_code, r.text)

def test_ab_test_conversion():
    payload = {
        "session_id": "test-session",
        "test_name": "DemoTest",
        "variant": "A",
        "conversion_type": "signup",
        "conversion_value": 1.0
    }
    r = requests.post(f"{BASE_URL}/api/ab-test/conversion", json=payload)
    print("POST /api/ab-test/conversion", r.status_code, r.text)

def test_lead_notify():
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
    r = requests.post(f"{BASE_URL}/api/lead/notify", json=payload)
    print("POST /api/lead/notify", r.status_code, r.text)

def test_lead_notify_high_score():
    # Try to notify with high-value lead
    payload = {
        "session_id": "test-session",
        "name": "High Value Lead",
        "email": "highvalue@example.com",
        "phone": "9999999999",
        "business_type": "Retail",
        "location": "City",
        "staff_size": "More than 15",
        "monthly_sales": "₹5L+",
        "features_interested": ["Billing / Invoicing", "Loans"]
    }
    r = requests.post(f"{BASE_URL}/api/lead/notify", json=payload)
    print("POST /api/lead/notify (high score)", r.status_code, r.text)

def test_generate_customer_id():
    payload = {"session_id": "test-session", "customer_data": {"name": "John Doe", "email": "john@example.com"}}
    r = requests.post(f"{BASE_URL}/api/customer/generate-id", json=payload)
    print("POST /api/customer/generate-id", r.status_code, r.text)

def test_get_customer_details():
    r = requests.get(f"{BASE_URL}/api/customer/test-customer")
    print("GET /api/customer/test-customer", r.status_code, r.text)

def test_tracking_page_entry():
    payload = {"session_id": "test-session", "page_identifier": "home"}
    r = requests.post(f"{BASE_URL}/api/tracking/page-entry", json=payload)
    print("POST /api/tracking/page-entry", r.status_code, r.text)

def test_tracking_page_exit():
    payload = {"session_id": "test-session", "page_tracking_id": "home"}
    r = requests.post(f"{BASE_URL}/api/tracking/page-exit", json=payload)
    print("POST /api/tracking/page-exit", r.status_code, r.text)

def test_tracking_journey():
    r = requests.get(f"{BASE_URL}/api/tracking/journey/test-session")
    print("GET /api/tracking/journey/test-session", r.status_code, r.text)

def test_tracking_customer_journey():
    r = requests.get(f"{BASE_URL}/api/tracking/customer-journey/test-customer")
    print("GET /api/tracking/customer-journey/test-customer", r.status_code, r.text)

def test_tracking_visual_journey():
    r = requests.get(f"{BASE_URL}/api/tracking/visual-journey/test-identifier")
    print("GET /api/tracking/visual-journey/test-identifier", r.status_code, r.text)

def test_cif_start():
    payload = {"session_id": "test-session", "customer_id": "cust-123"}
    r = requests.post(f"{BASE_URL}/api/cif/start", json=payload)
    print("POST /api/cif/start", r.status_code, r.text)

def test_cif_update():
    payload = {
        "customer_id": "cust-123",
        "form_data": {"basic_info": {"full_name": "Test Customer", "email": "test@example.com", "phone": "9876543210"}},
        "section": "basic_info"
    }
    r = requests.put(f"{BASE_URL}/api/cif/update", json=payload)
    print("PUT /api/cif/update", r.status_code, r.text)

def test_cif_complete():
    payload = {"customer_id": "cust-123", "form_data": {"basic_info": {"full_name": "Test Customer"}}}
    r = requests.post(f"{BASE_URL}/api/cif/complete", json=payload)
    print("POST /api/cif/complete", r.status_code, r.text)

def test_get_cif_data():
    r = requests.get(f"{BASE_URL}/api/cif/cust-123")
    print("GET /api/cif/cust-123", r.status_code, r.text)

def test_session_exit():
    payload = {"session_id": "test-session"}
    r = requests.post(f"{BASE_URL}/api/session/exit", json=payload)
    print("POST /api/session/exit", r.status_code, r.text)

def test_analytics_drop_off_points():
    r = requests.get(f"{BASE_URL}/api/analytics/drop-off-points")
    print("GET /api/analytics/drop-off-points", r.status_code, r.text)

def test_analytics_page_performance():
    r = requests.get(f"{BASE_URL}/api/analytics/page-performance")
    print("GET /api/analytics/page-performance", r.status_code, r.text)

def test_analytics_customer_journey():
    r = requests.get(f"{BASE_URL}/api/analytics/customer-journey")
    print("GET /api/analytics/customer-journey", r.status_code, r.text)

def test_analytics_cif_completion():
    r = requests.get(f"{BASE_URL}/api/analytics/cif-completion")
    print("GET /api/analytics/cif-completion", r.status_code, r.text)

def run_all():
    test_root()
    test_next_question()
    test_session_start()
    test_get_questions()
    test_answer()
    test_answer_with_conditional()
    test_skip_question()
    test_log_behavior()
    test_get_behavior_actions()
    test_update_lead_profile()
    test_update_lead_profile_high_score()
    test_get_lead_summary()
    test_export_lead_data()
    test_sync_lead_odoo()
    test_get_score()
    test_get_product_menu()
    test_get_cta_options()
    test_get_leads_analytics()
    test_ab_test_variant()
    test_ab_test_conversion()
    test_lead_notify()
    test_lead_notify_high_score()
    test_generate_customer_id()
    test_get_customer_details()
    test_tracking_page_entry()
    test_tracking_page_exit()
    test_tracking_journey()
    test_tracking_customer_journey()
    test_tracking_visual_journey()
    test_cif_start()
    test_cif_update()
    test_cif_complete()
    test_get_cif_data()
    test_session_exit()
    test_analytics_drop_off_points()
    test_analytics_page_performance()
    test_analytics_customer_journey()
    test_analytics_cif_completion()

if __name__ == "__main__":
    run_all()
