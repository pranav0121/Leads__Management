# Backend-only workflow configuration. No frontend/static logic.
# Workflow Configuration
WORKFLOW_CONFIG = {
    "scoring": {
        "session_opened": 5,
        "replied_to_greeting": 5,
        "answered_question": 5,
        "answered_all_questions": 10,
        "shared_contact": 10,
        "clicked_product": 5,
        "clicked_pricing": 10,
        "clicked_demo": 15,
        "meaningful_reply": 10,
        "quick_reply": 5,  # < 20 seconds
        "detailed_answer": 5,  # > 10 characters
        "cta_clicked": 15,
        "early_dropout": -10,
        "ignored_cta": 0,
        "completed_journey": 10,
        "question_skipped": 0  # No penalty for skipping questions
    },

    "lead_thresholds": {
        "sql": 60,  # Sales Qualified Lead
        "mql": 30,  # Marketing Qualified Lead
        "unqualified": 0
    },

    "questions_workflow": [
        {
            "id": 1,
            "step": "greeting",
            "question_text": "Hi! Welcome to YouShop/YouResto — your smart business partner. Let's help you get started 🚀\n\nCan I ask a few quick questions to customize your solution?",
            "question_type": "single_choice",
            "options": ["Yes, go ahead", "What is this about?", "No thanks"],
            "base_score": 5,
            "required": True,
            "order_index": 1
        },
        {
            "id": 2,
            "step": "profile",
            "question_text": "What type of business do you run?",
            "question_type": "single_choice",
            "options": ["Kirana / Retail Shop", "Restaurant / Café", "Wholesale / FMCG", "Other"],
            "base_score": 5,
            "required": True,
            "order_index": 2
        },
        {
            "id": 3,
            "step": "profile",
            "question_text": "Where is your shop located?",
            "question_type": "text",
            "options": None,
            "base_score": 5,
            "required": True,
            "order_index": 3
        },
        {
            "id": 4,
            "step": "profile",
            "question_text": "How many staff members work with you?",
            "question_type": "single_choice",
            "options": ["Just me", "2–5", "6–15", "More than 15"],
            "base_score": 5,
            "required": True,
            "order_index": 4
        },
        {
            "id": 5,
            "step": "profile",
            "question_text": "What's your monthly sales volume? (approx.)",
            "question_type": "single_choice",
            "options": ["Less than ₹50K", "₹50K – ₹2L", "₹2L – ₹5L", "₹5L+"],
            "base_score": 5,
            "required": True,
            "order_index": 5
        },
        {
            "id": 6,
            "step": "profile",
            "question_text": "What do you need help with?",
            "question_type": "multiple_choice",
            "options": ["Billing / Invoicing", "QR Payments", "Staff/HR", "Inventory", "Online Store", "WhatsApp Marketing", "Loans"],
            "base_score": 5,
            "required": True,
            "order_index": 6
        },
        {
            "id": 7,
            "step": "contact",
            "question_text": "Can we get your contact details to send your custom setup or offers?",
            "question_type": "contact_form",
            "options": ["Share Phone", "Share Email", "Skip for now"],
            "base_score": 10,
            "required": False,
            "order_index": 7
        }
    ],

    # Special responses for greeting question
    "greeting_responses": {
        "What is this about?": {
            "response_type": "about_info",
            "title": "About YouShop/YouResto",
            "content": "YouShop/YouResto is your all-in-one smart business partner designed to help small and medium businesses thrive in today's digital world.\n\n🚀 **What we offer:**\n• Digital billing & invoicing (GST compliant)\n• QR code payments & digital transactions\n• Inventory management\n• Staff & HR management\n• Online store creation\n• WhatsApp business tools\n• Business loans & financial solutions\n\n💡 **Why choose us:**\n• Easy to use, works offline\n• Affordable pricing for all business sizes\n• 24/7 customer support\n• Trusted by thousands of businesses\n\nWould you like to see how we can help your specific business? Just let us know what type of business you run!",
            "next_action": "continue_to_business_type"
        },
        "No thanks": {
            "response_type": "thank_you",
            "title": "Thank You!",
            "content": "Thank you for your time! 🙏\n\nWe understand that every business has different needs and timing. If you ever want to explore how YouShop/YouResto can help grow your business, we'll be here.\n\n📞 **Quick ways to reach us:**\n• Call: +91-XXXXXXXXX\n• WhatsApp: +91-XXXXXXXXX\n• Email: support@youshop.com\n\n🎁 **Special offer:** When you're ready, mention code 'WELCOME20' for 20% off your first month!\n\nWishing you success in your business journey! 🌟",
            "next_action": "end_session"
        },
        "Yes, go ahead": {
            "response_type": "continue_flow",
            "next_action": "continue_to_business_type"
        }
    },

    "product_menu": [
        {"id": "billing", "title": "📊 Billing & Invoicing",
            "description": "GST-compliant billing and invoicing", "score": 5},
        {"id": "inventory", "title": "📦 Inventory",
            "description": "Track and manage your stock", "score": 5},
        {"id": "qr_payments", "title": "💳 QR / Payments",
            "description": "Accept digital payments easily", "score": 5},
        {"id": "staff_hr", "title": "👥 Staff & HR",
            "description": "Manage your team efficiently", "score": 5},
        {"id": "online_selling", "title": "🛒 Online Selling",
            "description": "Sell online and reach more customers", "score": 5},
        {"id": "whatsapp_tools", "title": "💬 WhatsApp Tools",
            "description": "Business communication tools", "score": 5},
        {"id": "loans_offers", "title": "💰 Loans & Offers",
            "description": "Financial solutions for your business", "score": 5},
        {"id": "demo", "title": "🎥 Watch Demo",
            "description": "See our products in action", "score": 15},
        {"id": "other", "title": "❓ Other Questions",
            "description": "Get help with anything else", "score": 5}
    ],

    "cta_options": [
        {"id": "talk_to_sales", "title": "🤝 Talk to Sales Rep",
            "description": "Connect with our sales team", "score": 15},
        {"id": "request_callback", "title": "📞 Request Callback",
            "description": "We'll call you back", "score": 15},
        {"id": "start_trial", "title": "🚀 Start Free Trial",
            "description": "Try our products for free", "score": 15},
        {"id": "restart_bot", "title": "🔄 Restart Bot",
            "description": "Start the conversation over", "score": 0},
        {"id": "human_help", "title": "❓ Need Human Help",
            "description": "Connect with our support team", "score": 10}
    ]
}

# Feature-specific FAQs
FEATURE_FAQS = {
    "billing": {
        "title": "Our billing app is GST-compliant, works offline, supports barcodes & invoices.",
        "faqs": [
            "How does it work?",
            "What devices does it support?",
            "Can I print invoices?",
            "Can I try a demo?"
        ]
    },
    "qr_payments": {
        "title": "Accept payments via UPI, card, QR, wallets, and track them easily.",
        "faqs": [
            "How do I get my QR?",
            "How do settlements work?",
            "Is it free to use?"
        ]
    },
    "whatsapp_tools": {
        "title": "Use WhatsApp to send invoices, take orders, or run promotions.",
        "faqs": [
            "How does WhatsApp Ordering work?",
            "Can I send bulk messages?",
            "How much does this cost?"
        ]
    }
}
