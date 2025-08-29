# Leads Management Backend (FastAPI)

## Overview

An advanced backend for lead capture, scoring, and qualification, built with FastAPI and PostgreSQL. This system powers chatbot workflows, tracks user behavior, classifies leads (SQL/MQL/Unqualified), supports notifications, A/B testing, analytics, UTM tracking, CTA options, and workflow configuration for CRM and sales teams. Now includes:

- Categorized endpoints in Swagger UI for easier API exploration
- GET endpoint to list valid user actions (`/api/behavior/actions`)
- Expanded API-level test coverage (all endpoints tested)
- Pydantic v2+ compatibility
- Workspace cleanup for production readiness

## Features

- RESTful API for chatbot and frontend integration
- Dynamic question flow and behavioral scoring
- Automatic lead qualification (SQL/MQL/Unqualified)
- Multi-channel notifications (Email, Slack, Discord)
- A/B testing framework for optimization
- Analytics dashboard endpoint
- UTM source tracking for marketing attribution
- Configurable CTA (Call-to-Action) options
- Centralized workflow configuration
- PostgreSQL + SQLAlchemy ORM
- Comprehensive unit and API-level tests
- Categorized endpoints in Swagger UI
- GET endpoint for valid user actions
- Pydantic v2+ compatibility
- Workspace cleaned for production

## Architecture & Main Files

- **main.py**: FastAPI app entrypoint, CORS enabled
- **router.py**: All API endpoints (session, questions, answers, profile, analytics, notifications, A/B testing)
- **services.py**: Business logic (LeadService, ScoringService, QuestionService, AnswerService)
- **models.py**: SQLAlchemy models for Lead, Answer, UserBehavior
- **workflow_config.py**: Centralized config for questions, scoring, thresholds, product menu, CTA options
- **notification_service.py**: Notification logic (Email, Slack, Discord)
- **ab_testing_service.py**: A/B test assignment, conversion logging, results
- **database.py**: DB connection/session management
- **config.py**: App and notification config (reads from .env)
- **test_services.py**: Unit tests for all major logic and endpoints

## Recent Improvements

- **Endpoint Categorization:** All endpoints are grouped and described in Swagger UI for easier navigation.
- **GET /api/behavior/actions:** Returns a list of valid user actions for logging behaviors.
- **Expanded Testing:** All endpoints and business logic are covered by FastAPI TestClient-based API tests.
- **Pydantic v2+ Compatibility:** All request/response models updated for latest Pydantic standards.
- **Workspace Cleanup:** Removed unnecessary files and ensured production readiness.

## Setup & Installation

1. **Clone & Setup**
   ```bash
   git clone <repo-url>
   cd Leads_Management
   python -m venv venv
   venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```
2. **Configure Database**
   - Create a PostgreSQL DB and user
   - Set credentials in `.env`
3. **Run Migrations (Important for existing databases)**

   ```bash
   # For new installations
   python -c "from database import Base, engine; Base.metadata.create_all(engine)"

   # For existing databases with old answer structure, run migration first
   python migrate_answers_table.py
   ```

4. **Start API Server**
   ```bash
   uvicorn main:app --reload
   ```
5. **Run Tests**
   ```bash
   pytest
   ```

## Setup Instructions

1. Clone the repository:

   ```bash
   git clone https://github.com/pranav0121/Leads__Management.git
   ```

2. Navigate to the project directory:

   ```bash
   cd Leads__Management
   ```

3. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Set up the environment variables:

   - Copy `.env.example` to `.env` and fill in the required values.

6. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

## Testing Instructions

1. Run all tests:

   ```bash
   pytest
   ```

2. Run tests with detailed output:

   ```bash
   pytest -v
   ```

3. Run specific tests:
   ```bash
   pytest path/to/test_file.py
   ```

## API Endpoints (Categorized)

### 1. Session & Question Flow

- `POST /api/session/start` — Start a new lead session (returns session_id)
- `GET /api/questions` — Get the full list of questions (for custom flows or review)
- `POST /api/next-question` — Get the next unanswered required question after answering (for guided flows)
- `POST /api/answer` — Log an answer to a question (simplified: only session_id and answer_text required)
- `POST /api/skip-question` — Allow users to skip questions without penalty

### 2. User Actions & Behaviors

- `POST /api/behavior` — Log user actions (e.g., contact shared, CTA clicked, demo clicked)
- `GET /api/behavior/actions` — List all valid user actions for logging (for frontend validation)

### 3. Lead Profile & Data

- `POST /api/lead/profile` — Update lead profile (name, email, business type, etc.)
- `GET /api/lead/summary/{session_id}` — Get full lead summary (for CRM/export)
- `GET /api/lead/export/{session_id}` — Export lead data in CRM format

### 4. Scoring & Qualification

- `GET /api/score/{session_id}` — Get current lead score and qualification (SQL/MQL/Unqualified)

### 5. Product & CTA Options

- `GET /api/product-menu` — Get available product/service options
- `GET /api/cta-options` — Get available call-to-action options

### 6. Analytics & Reporting

- `GET /api/analytics/leads` — Get analytics dashboard (lead counts, conversion rate, average score, completion rate)

### 7. A/B Testing

- `POST /api/ab-test/variant` — Get assigned A/B test variant for a session
- `POST /api/ab-test/conversion` — Log a conversion event for A/B test analysis

### 8. Notifications

- `POST /api/lead/notify` — Trigger sales team notification for high-value (SQL) leads

---

## UTM Tracking

- UTM source is captured at session start (`utm_source` field) and stored with each lead.
- Enables marketing attribution and campaign performance analysis.

## CTA (Call-to-Action) Options

- Configured in `workflow_config.py` under `cta_options`.
- API: `GET /api/cta-options` returns available CTAs (e.g., Talk to Sales, Request Callback, Start Trial).
- Each CTA has a score impact and description for frontend display.

## Workflow Configuration

- All questions, scoring rules, product menu, and CTA options are defined in `workflow_config.py`.
- Easy to update question flow, scoring, and qualification thresholds without code changes.
- API: `GET /api/questions`, `GET /api/product-menu`, `GET /api/cta-options` use this config.

## A/B Testing

- Assigns users to variants for message/question/CTA experiments (see `ab_testing_service.py`).
- API: `POST /api/ab-test/variant` assigns and returns variant; `POST /api/ab-test/conversion` logs conversion.
- Results and winning variants can be analyzed for optimization.

## Scoring & Lead Qualification

- Actions (session opened, answered question, shared contact, CTA click, etc.) earn points.
- Score thresholds: SQL ≥ 60, MQL ≥ 30, else Unqualified.
- All scoring rules and workflow are in `workflow_config.py`.

## Notifications

- Only SQL leads (score ≥ 60) trigger notifications.
- Supports Email, Slack, Discord (see `notification_service.py`).

## Analytics

- `/api/analytics/leads` returns total leads, SQL/MQL/unqualified counts, conversion rate, average score, completion rate.

## Environment Variables (`.env`)

- `DATABASE_URL` — PostgreSQL connection string
- `SENDER_EMAIL`, `SENDER_PASSWORD`, `SALES_TEAM_EMAILS` — Notification settings
- `SLACK_WEBHOOK_URL`, `DISCORD_WEBHOOK_URL` — Webhook URLs
- `AB_TESTING_ENABLED`, `ANALYTICS_RETENTION_DAYS`, etc.

## Testing & Development

- All business logic and endpoints are covered by unit and API-level tests in `test_services.py` using FastAPI TestClient.
- Use `pytest` to run tests. All 25+ tests pass, covering every endpoint and major logic branch.
- Code follows PEP8 and is ready for production. Workspace is cleaned of unnecessary files.

## Contributing

- Fork, branch, and submit PRs.
- Add tests for new features.
- Use clear commit messages.

## Changelog (Recent Updates)

- **Simplified Answer Structure**: Answers table now only contains session_id, answer_text, and created_at columns
- **Skip Question Feature**: Added `/api/skip-question` endpoint allowing users to skip questions without penalty
- **Flexible Question Flow**: Users can now skip any question and continue with the flow
- Added GET /api/behavior/actions endpoint
- Categorized endpoints in Swagger UI
- Expanded API-level test coverage
- Updated for Pydantic v2+
- Workspace cleaned for production
