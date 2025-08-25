#!/usr/bin/env python3
"""
Demo script to test the new page tracking GET endpoints
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"


def test_page_tracking_endpoints():
    print("🚀 Testing Page Tracking GET Endpoints")
    print("=" * 60)

    try:
        # 1. Start a session
        print("\n1. Starting a new session...")
        session_response = requests.post(f"{BASE_URL}/api/session/start",
                                         json={"utm_source": "demo_tracking"})
        session_data = session_response.json()
        session_id = session_data["session_id"]
        print(f"✅ Session ID: {session_id}")

        # 2. Generate customer ID
        print("\n2. Generating customer ID...")
        customer_response = requests.post(f"{BASE_URL}/api/customer/generate-id",
                                          json={"session_id": session_id})
        customer_data = customer_response.json()
        customer_id = customer_data["customer_id"]
        print(f"✅ Customer ID: {customer_id}")

        # 3. Simulate page tracking
        print("\n3. Simulating page navigation...")

        pages = [
            {"page": "welcome_page", "question_id": 1, "type": "question"},
            {"page": "business_type_page", "question_id": 2, "type": "question"},
            {"page": "location_page", "question_id": 3, "type": "question"},
            {"page": "contact_form", "question_id": None, "type": "form"},
            {"page": "thank_you", "question_id": None, "type": "completion"}
        ]

        page_tracking_ids = []

        for i, page_info in enumerate(pages):
            print(f"   📄 Entering page: {page_info['page']}")

            # Log page entry
            entry_response = requests.post(f"{BASE_URL}/api/tracking/page-entry", json={
                "session_id": session_id,
                "page_identifier": page_info['page'],
                "question_id": page_info['question_id'],
                "page_type": page_info['type'],
                "metadata": {"step": i + 1, "page_title": page_info['page'].replace('_', ' ').title()}
            })

            if entry_response.status_code == 200:
                page_tracking_id = entry_response.json()["page_tracking_id"]
                page_tracking_ids.append(page_tracking_id)

                # Simulate time spent on page (2-5 seconds)
                time_spent = 2 + i
                time.sleep(1)  # Small delay for demo

                # Log page exit
                exit_response = requests.post(f"{BASE_URL}/api/tracking/page-exit", json={
                    "page_tracking_id": page_tracking_id
                })

                print(f"   ✅ Page tracked (ID: {page_tracking_id})")
            else:
                print(f"   ❌ Failed to track page: {entry_response.text}")

        print(f"\n✅ Tracked {len(page_tracking_ids)} pages")

        # 4. Test GET endpoints
        print("\n" + "=" * 60)
        print("🔍 TESTING GET ENDPOINTS")
        print("=" * 60)

        # Test journey by session ID
        print(f"\n1. GET Journey by Session ID: {session_id}")
        print("-" * 40)
        journey_response = requests.get(
            f"{BASE_URL}/api/tracking/journey/{session_id}")
        if journey_response.status_code == 200:
            journey_data = journey_response.json()
            print(f"✅ Found {len(journey_data['journey'])} pages in journey")
            for i, page in enumerate(journey_data['journey']):
                print(
                    f"   Step {i+1}: {page['page']} (Time: {page.get('time_spent', 0)}s)")
        else:
            print(f"❌ Error: {journey_response.text}")

        # Test journey by customer ID
        print(f"\n2. GET Journey by Customer ID: {customer_id}")
        print("-" * 40)
        customer_journey_response = requests.get(
            f"{BASE_URL}/api/tracking/customer-journey/{customer_id}")
        if customer_journey_response.status_code == 200:
            customer_journey_data = customer_journey_response.json()
            print(f"✅ Customer Journey Summary:")
            print(
                f"   📊 Total Pages: {customer_journey_data['summary']['total_pages_visited']}")
            print(
                f"   ⏱️  Total Time: {customer_journey_data['summary']['total_time_spent']}s")
            print(
                f"   📈 Status: {customer_journey_data['summary']['completion_status']}")
        else:
            print(f"❌ Error: {customer_journey_response.text}")

        # Test visual journey
        print(f"\n3. GET Visual Journey by Customer ID: {customer_id}")
        print("-" * 40)
        visual_response = requests.get(
            f"{BASE_URL}/api/tracking/visual-journey/{customer_id}?id_type=customer")
        if visual_response.status_code == 200:
            visual_data = visual_response.json()
            print(f"✅ Visual Journey Statistics:")
            stats = visual_data['statistics']
            print(f"   📊 Total Pages: {stats['total_pages']}")
            print(f"   ⏱️  Total Time: {stats['total_time_formatted']}")
            print(f"   📈 Completion Rate: {stats['completion_rate']}")
            print(f"   ⚡ Avg Time/Page: {stats['average_time_per_page']}")

            print(f"\n📋 Journey Steps:")
            for step in visual_data['visual_journey']:
                status_icon = "✅" if step['status'] == 'completed' else "🔄"
                print(
                    f"   {status_icon} Step {step['step']}: {step['page_name']} ({step['time_spent_formatted']})")
        else:
            print(f"❌ Error: {visual_response.text}")

        print("\n" + "=" * 60)
        print("🎉 PAGE TRACKING DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"📝 Session ID: {session_id}")
        print(f"🆔 Customer ID: {customer_id}")
        print("\n🔗 Available GET Endpoints:")
        print(f"   1. /api/tracking/journey/{session_id}")
        print(f"   2. /api/tracking/customer-journey/{customer_id}")
        print(
            f"   3. /api/tracking/visual-journey/{customer_id}?id_type=customer")
        print(
            f"   4. /api/tracking/visual-journey/{session_id}?id_type=session")

    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to server. Make sure FastAPI server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_page_tracking_endpoints()
