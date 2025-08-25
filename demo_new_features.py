#!/usr/bin/env python3
"""
Demo script showcasing all new Customer Tracking features:
- Customer ID generation and management
- Page-by-page tracking
- Customer Information Form (CIF)
- Session exit tracking
- Advanced analytics
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
DEMO_UTM_SOURCE = "demo_campaign"


def print_section(title):
    print(f"\n{'='*60}")
    print(f"🚀 {title}")
    print(f"{'='*60}")


def print_result(step, data):
    print(f"✅ {step}")
    print(json.dumps(data, indent=2))
    print("-" * 40)


def demo_customer_journey():
    """Demonstrate complete customer journey with new tracking features"""

    print_section("COMPREHENSIVE CUSTOMER TRACKING DEMO")

    # 1. Start Session
    print_section("1. SESSION INITIALIZATION")
    session_data = {"utm_source": DEMO_UTM_SOURCE}
    response = requests.post(
        f"{BASE_URL}/api/session/start", json=session_data)
    session_result = response.json()
    session_id = session_result["session_id"]
    print_result("Session Started", session_result)

    # 2. Generate Customer ID
    print_section("2. CUSTOMER ID GENERATION")
    customer_response = requests.post(
        f"{BASE_URL}/api/customer/generate-id", json={"session_id": session_id})
    customer_result = customer_response.json()
    customer_id = customer_result["customer_id"]
    print_result("Customer ID Generated", customer_result)

    # 3. Start Customer Information Form
    print_section("3. CUSTOMER INFORMATION FORM (CIF) SETUP")
    cif_start_response = requests.post(f"{BASE_URL}/api/cif/start", json={
        "session_id": session_id,
        "customer_id": customer_id
    })
    print_result("CIF Started", cif_start_response.json())

    # 4. Simulate Page Tracking Through Questions
    print_section("4. PAGE-BY-PAGE TRACKING SIMULATION")

    questions_response = requests.get(f"{BASE_URL}/api/questions")
    questions = questions_response.json()

    page_tracking_ids = []

    for i, question in enumerate(questions[:3]):  # Demo first 3 questions
        # Log page entry
        page_entry_response = requests.post(f"{BASE_URL}/api/tracking/page-entry", json={
            "session_id": session_id,
            "page_identifier": f"question_{question['id']}",
            "question_id": question['id'],
            "page_type": "question",
            "metadata": {"question_text": question['question_text'][:50]}
        })
        page_tracking_id = page_entry_response.json()["page_tracking_id"]
        page_tracking_ids.append(page_tracking_id)
        print_result(
            f"Page Entry - Question {question['id']}", page_entry_response.json())

        # Simulate time spent on page
        time.sleep(1)

        # Answer the question
        answer_response = requests.post(f"{BASE_URL}/api/answer", json={
            "session_id": session_id,
            "question_id": question['id'],
            "answer_text": f"Demo answer for question {question['id']}",
            "time_taken": 15.5
        })
        print_result(
            f"Answer Logged - Question {question['id']}", answer_response.json())

        # Log page exit
        page_exit_response = requests.post(f"{BASE_URL}/api/tracking/page-exit", json={
            "page_tracking_id": page_tracking_id
        })
        print_result(
            f"Page Exit - Question {question['id']}", page_exit_response.json())

    # 5. Update CIF with Comprehensive Data
    print_section("5. COMPREHENSIVE CIF DATA COLLECTION")

    # Basic Information
    basic_info = {
        "full_name": "John Demo Customer",
        "email": "john.demo@example.com",
        "phone": "+91-9876543210",
        "alternate_phone": "+91-9876543211"
    }
    requests.put(f"{BASE_URL}/api/cif/update", json={
        "customer_id": customer_id,
        "form_data": basic_info,
        "section": "basic_info"
    })
    print_result("Basic Info Updated", basic_info)

    # Business Details
    business_details = {
        "business_name": "Demo Enterprises Pvt Ltd",
        "business_type": "Retail",
        "industry": "Fashion & Apparel",
        "registration_number": "GST123456789012345",
        "business_address": {
            "street": "123 Demo Street, Commercial Complex",
            "city": "Mumbai",
            "state": "Maharashtra",
            "pincode": "400001"
        }
    }
    requests.put(f"{BASE_URL}/api/cif/update", json={
        "customer_id": customer_id,
        "form_data": business_details,
        "section": "business_details"
    })
    print_result("Business Details Updated", business_details)

    # Operational Information
    operational_info = {
        "staff_size": "6-15 employees",
        "monthly_sales": "₹2L-₹5L",
        "operating_hours": "9 AM - 9 PM",
        "peak_season": "Festival Season (Oct-Dec)"
    }
    requests.put(f"{BASE_URL}/api/cif/update", json={
        "customer_id": customer_id,
        "form_data": operational_info,
        "section": "operational_info"
    })
    print_result("Operational Info Updated", operational_info)

    # Technology Profile
    technology_profile = {
        "current_pos": "Manual Billing with Calculator",
        "payment_methods": ["Cash", "UPI", "Credit/Debit Cards"],
        "features_needed": ["Billing", "Inventory Management", "QR Payments", "Customer Database"],
        "tech_comfort_level": "Beginner"
    }
    requests.put(f"{BASE_URL}/api/cif/update", json={
        "customer_id": customer_id,
        "form_data": technology_profile,
        "section": "technology_profile"
    })
    print_result("Technology Profile Updated", technology_profile)

    # Financial Information
    financial_info = {
        "annual_revenue": "₹10L-₹50L",
        "growth_stage": "Expanding to new locations",
        "investment_capacity": "₹50K-₹1L for technology upgrade"
    }
    requests.put(f"{BASE_URL}/api/cif/update", json={
        "customer_id": customer_id,
        "form_data": financial_info,
        "section": "financial_info"
    })
    print_result("Financial Info Updated", financial_info)

    # 6. Log User Behaviors
    print_section("6. USER BEHAVIOR TRACKING")

    behaviors = [
        {"action": "contact_shared", "metadata": {"method": "phone"}},
        {"action": "cta_clicked", "metadata": {"cta_type": "request_demo"}},
        {"action": "product_interest", "metadata": {"product": "POS System"}},
        {"action": "pricing_viewed", "metadata": {"plan": "Professional"}}
    ]

    for behavior in behaviors:
        behavior_response = requests.post(f"{BASE_URL}/api/behavior", json={
            "session_id": session_id,
            "action": behavior["action"],
            "metadata": behavior.get("metadata")
        })
        print_result(
            f"Behavior Logged: {behavior['action']}", behavior_response.json())

    # 7. Update Lead Profile
    print_section("7. LEAD PROFILE COMPLETION")

    profile_data = {
        "name": "John Demo Customer",
        "email": "john.demo@example.com",
        "phone": "+91-9876543210",
        "business_type": "Retail",
        "location": "Mumbai, Maharashtra",
        "staff_size": "6-15",
        "monthly_sales": "₹2L-₹5L",
        "features_interested": ["Billing", "Inventory", "QR Payments"]
    }

    profile_response = requests.post(f"{BASE_URL}/api/lead/profile", json={
        "session_id": session_id,
        "profile_data": profile_data
    })
    print_result("Lead Profile Updated", profile_response.json())

    # 8. Get Current Lead Score
    print_section("8. LEAD SCORING & QUALIFICATION")

    score_response = requests.get(f"{BASE_URL}/api/score/{session_id}")
    score_result = score_response.json()
    print_result("Current Lead Score", score_result)

    # 9. Complete CIF
    print_section("9. CIF COMPLETION")

    complete_response = requests.post(f"{BASE_URL}/api/cif/complete", json={
        "customer_id": customer_id,
        "form_data": {}  # Final completion
    })
    print_result("CIF Completed", complete_response.json())

    # 10. Get Complete Customer Details
    print_section("10. COMPREHENSIVE CUSTOMER PROFILE")

    customer_details_response = requests.get(
        f"{BASE_URL}/api/customer/{customer_id}")
    customer_details = customer_details_response.json()
    print_result("Complete Customer Profile", customer_details)

    # 11. Get Customer Journey
    print_section("11. CUSTOMER JOURNEY ANALYSIS")

    journey_response = requests.get(
        f"{BASE_URL}/api/tracking/journey/{session_id}")
    journey_result = journey_response.json()
    print_result("Complete Customer Journey", journey_result)

    # 12. Get Final CIF Data
    print_section("12. FINAL CIF DATA")

    final_cif_response = requests.get(f"{BASE_URL}/api/cif/{customer_id}")
    final_cif = final_cif_response.json()
    print_result("Final CIF Data", final_cif)

    # 13. Simulate Session Exit (Completed)
    print_section("13. SESSION COMPLETION")

    session_exit_response = requests.post(f"{BASE_URL}/api/session/exit", json={
        "session_id": session_id,
        "exit_reason": "completed",
        "exit_page": "summary",
        "last_action": "form_completed",
        "metadata": {"completion_time": datetime.now().isoformat()}
    })
    print_result("Session Exit Logged", session_exit_response.json())

    # 14. Analytics Dashboard
    print_section("14. ANALYTICS & INSIGHTS")

    # General analytics
    analytics_response = requests.get(f"{BASE_URL}/api/analytics/leads")
    print_result("Lead Analytics", analytics_response.json())

    # Drop-off analytics
    dropoff_response = requests.get(
        f"{BASE_URL}/api/analytics/drop-off-points")
    print_result("Drop-off Analytics", dropoff_response.json())

    print_section("🎉 DEMO COMPLETED SUCCESSFULLY!")
    print(f"Customer ID: {customer_id}")
    print(f"Session ID: {session_id}")
    print(f"UTM Source: {DEMO_UTM_SOURCE}")
    print(f"Final Lead Score: {score_result.get('lead_score', 'N/A')}")
    print(f"Lead Classification: {score_result.get('lead_type', 'N/A')}")
    print(f"CIF Completion: {final_cif.get('completion_percentage', 0)}%")


def demo_abandonment_scenario():
    """Demonstrate abandoned session tracking"""

    print_section("ABANDONMENT SCENARIO DEMO")

    # Start session
    session_data = {"utm_source": "abandonment_test"}
    response = requests.post(
        f"{BASE_URL}/api/session/start", json=session_data)
    session_id = response.json()["session_id"]

    # Generate customer ID
    customer_response = requests.post(
        f"{BASE_URL}/api/customer/generate-id", json={"session_id": session_id})
    customer_id = customer_response.json()["customer_id"]

    # Answer only 2 questions then abandon
    questions_response = requests.get(f"{BASE_URL}/api/questions")
    questions = questions_response.json()

    for i in range(2):  # Only answer 2 questions
        question = questions[i]

        # Log page entry
        requests.post(f"{BASE_URL}/api/tracking/page-entry", json={
            "session_id": session_id,
            "page_identifier": f"question_{question['id']}",
            "question_id": question['id'],
            "page_type": "question"
        })

        # Answer question
        requests.post(f"{BASE_URL}/api/answer", json={
            "session_id": session_id,
            "question_id": question['id'],
            "answer_text": f"Partial answer {i+1}",
            "time_taken": 10.0
        })

    # Simulate abandonment at question 3
    abandonment_response = requests.post(f"{BASE_URL}/api/session/exit", json={
        "session_id": session_id,
        "exit_reason": "abandoned",
        "exit_question_id": questions[2]['id'],
        "exit_page": f"question_{questions[2]['id']}",
        "last_action": "navigated_away",
        "metadata": {"abandonment_reason": "too_many_questions"}
    })

    print_result("Abandonment Logged", abandonment_response.json())
    print(f"Abandoned at Question: {questions[2]['id']}")
    print(f"Customer ID: {customer_id}")


if __name__ == "__main__":
    print("🚀 Starting Comprehensive Customer Tracking Demo")
    print("Make sure the FastAPI server is running on http://localhost:8000")

    try:
        # Test server connectivity
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✅ Server is running!")

            # Run complete customer journey demo
            demo_customer_journey()

            # Wait before abandonment demo
            print("\n" + "="*60)
            print("⏳ Starting abandonment scenario in 3 seconds...")
            time.sleep(3)

            # Run abandonment scenario
            demo_abandonment_scenario()

        else:
            print("❌ Server is not responding correctly")

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Please start the FastAPI server first:")
        print("   uvicorn main:app --reload")
    except Exception as e:
        print(f"❌ Error running demo: {e}")
