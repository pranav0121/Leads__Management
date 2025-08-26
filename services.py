import os
import xmlrpc.client
import json
from datetime import datetime, date
from models import Question, Answer, Lead, UserBehavior, CustomerInformationForm, PageTracking, SessionExit
from database import get_db_session
from workflow_config import WORKFLOW_CONFIG
import time
import traceback
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

logging.info("Test log entry")


class QuestionService:
    @staticmethod
    def get_questions():
        """Fetch predefined questions from configuration."""
        logging.info("Fetching predefined questions from configuration.")
        return WORKFLOW_CONFIG['questions_workflow']


class AnswerService:
    @staticmethod
    def log_answer(session_id, question_id, answer_text, time_taken=None):
        """Log a single answer to the database."""
        db_session = get_db_session()
        try:
            logging.info(f"Logging answer for session_id={session_id}, question_id={question_id}.")
            logging.debug(f"Answer details: {answer_text}, time_taken={time_taken}.")

            # Calculate score for this answer
            score = ScoringService.calculate_answer_score(
                question_id, answer_text, time_taken)

            new_answer = Answer(
                session_id=session_id,
                question_id=question_id,
                answer_text=answer_text,
                time_taken=time_taken,
                score_earned=score
            )
            db_session.add(new_answer)

            # Update lead total score
            LeadService.update_lead_score(session_id, score)

            db_session.commit()
            return True, score
        except Exception as e:
            logging.error(f"Error logging answer: {e}")
            db_session.rollback()
            return False, 0
        finally:
            db_session.close()


class ScoringService:
    @staticmethod
    def get_scoring_map():
        """Get scoring configuration."""
        return WORKFLOW_CONFIG['scoring']

    @staticmethod
    def get_lead_thresholds():
        """Get lead qualification thresholds."""
        return WORKFLOW_CONFIG['lead_thresholds']

    @staticmethod
    def calculate_answer_score(question_id, answer_text, time_taken=None):
        """Calculate score for a specific answer."""
        logging.info("Calculating score for answer.")
        logging.debug(f"Question ID: {question_id}, Answer Text: {answer_text}, Time Taken: {time_taken}.")
        scoring_map = ScoringService.get_scoring_map()
        base_score = 5  # Default base score
        bonus_score = 0

        # Bonus for detailed answers (> 10 characters for text fields)
        if len(answer_text.strip()) > 10:
            bonus_score += scoring_map['detailed_answer']

        # Bonus for quick replies (< 120 seconds)
        if time_taken and time_taken < 120:
            bonus_score += scoring_map['quick_reply']

        return base_score + bonus_score

    @staticmethod
    def log_behavior(session_id, action, metadata=None):
        """Log user behavior and return score change."""
        db_session = get_db_session()
        try:
            logging.info(f"Logging user behavior for session_id={session_id}, action={action}.")
            logging.debug(f"Behavior metadata: {metadata}.")

            scoring_map = ScoringService.get_scoring_map()
            score_change = scoring_map.get(action, 0)

            behavior = UserBehavior(
                session_id=session_id,
                action=action,
                score_change=score_change,
                behavior_metadata=json.dumps(metadata) if metadata else None
            )
            db_session.add(behavior)

            # Update lead total score
            LeadService.update_lead_score(session_id, score_change)

            db_session.commit()
            return score_change
        except Exception as e:
            logging.error(f"Error logging behavior: {e}")
            db_session.rollback()
            return 0
        finally:
            db_session.close()

    @staticmethod
    def calculate_lead_type(total_score):
        """Determine lead type based on total score."""
        thresholds = ScoringService.get_lead_thresholds()
        if total_score >= thresholds['sql']:
            return "SQL"  # Sales Qualified Lead
        elif total_score >= thresholds['mql']:
            return "MQL"  # Marketing Qualified Lead
        else:
            return "Unqualified"


class LeadService:
    @staticmethod
    def create_lead(session_id, utm_source=None):
        """Create a new lead session."""
        db_session = get_db_session()
        try:
            logging.info(f"Creating lead for session_id={session_id}, utm_source={utm_source}.")
            logging.debug(f"Lead details: session_id={session_id}, utm_source={utm_source}.")

            lead = Lead(
                session_id=session_id,
                utm_source=utm_source,
                lead_score=0
            )
            db_session.add(lead)
            print(
                f"[DEBUG] Added lead with session_id={session_id} to session. Attempting commit...")
            db_session.commit()
            print(f"[DEBUG] Commit successful for session_id={session_id}.")

            # Log session opened behavior
            ScoringService.log_behavior(session_id, 'session_opened')

            return True
        except Exception as e:
            logging.error(f"Error creating lead: {e}")
            db_session.rollback()
            from fastapi import HTTPException
            raise HTTPException(
                status_code=500, detail=f"Error creating lead: {e}")
        finally:
            db_session.close()

    @staticmethod
    def update_lead_score(session_id, score_change):
        """Update lead total score."""
        db_session = get_db_session()
        try:
            lead = db_session.query(Lead).filter_by(
                session_id=session_id).first()
            if lead:
                lead.lead_score += score_change
                lead.lead_type = ScoringService.calculate_lead_type(
                    lead.lead_score)
                db_session.commit()
        except Exception as e:
            print(f"Error updating lead score: {e}")
            db_session.rollback()
        finally:
            db_session.close()

    @staticmethod
    def update_lead_profile(session_id, profile_data):
        """Update lead profile information."""
        db_session = get_db_session()
        try:
            start_time = time.time()
            lead = db_session.query(Lead).filter_by(session_id=session_id).first()
            end_time = time.time()
            logging.info(f"Query execution time: {end_time - start_time} seconds")

            if lead:
                logging.info(f"Updating lead with session_id: {session_id}")
                logging.debug(f"Profile data: {profile_data}")

                # Update lead attributes from profile data
                for key, value in profile_data.items():
                    if hasattr(lead, key):
                        old_value = getattr(lead, key)
                        logging.info(f"Updating {key}: {old_value} -> {value}")
                        if key == 'features_interested' and isinstance(value, list):
                            setattr(lead, key, json.dumps(value))
                        else:
                            setattr(lead, key, value)

                logging.debug(f"Lead data before commit: {lead.__dict__}")
                db_session.commit()
                logging.info("Lead updated successfully.")
                return True

            logging.warning("Lead not found.")
            return False

        except Exception as e:
            logging.error(f"Error updating lead profile: {e}")
            logging.error(traceback.format_exc())
            db_session.rollback()
            return False

        finally:
            db_session.close()

    @staticmethod
    def get_lead_summary(session_id):
        """Get complete lead summary for CRM export."""
        db_session = get_db_session()
        try:
            lead = db_session.query(Lead).filter_by(
                session_id=session_id).first()
            if lead:
                # Calculate lead type based on current score
                lead_type = ScoringService.calculate_lead_type(lead.lead_score)

                # Update lead type in database
                lead.lead_type = lead_type
                db_session.commit()

                return {
                    'session_id': lead.session_id,
                    'name': lead.name,
                    'location': lead.location,
                    'business_type': lead.business_type,
                    'staff_size': lead.staff_size,
                    'monthly_sales': lead.monthly_sales,
                    'features_interested': json.loads(lead.features_interested) if lead.features_interested else [],
                    'contact_info': lead.phone or lead.email,
                    'email': lead.email,
                    'phone': lead.phone,
                    'lead_score': lead.lead_score,
                    'lead_type': lead_type,
                    'utm_source': lead.utm_source,
                    'created_at': lead.created_at.isoformat() if lead.created_at else None,
                    'updated_at': lead.updated_at.isoformat() if lead.updated_at else None
                }
            return None
        except Exception as e:
            print(f"Error getting lead summary: {e}")
            return None
        finally:
            db_session.close()


# Odoo Sync Service


class OdooSyncService:
    @staticmethod
    def sync_lead(session_id):
        # Get lead summary
        summary = LeadService.get_lead_summary(session_id)
        if not summary:
            return None
        # Prepare Odoo data
        lead_data = {
            "name": summary.get('name', 'Unknown'),
            "partner_name": summary.get('name', 'Unknown'),
            "city": summary.get('location', ''),
            "type": "opportunity",
            "x_business_type": summary.get('business_type', ''),
            "x_staff_size": summary.get('staff_size', ''),
            "x_monthly_sales": summary.get('monthly_sales', ''),
            "x_features_interested": ', '.join(summary.get('features_interested', [])),
            "phone": summary.get('phone', ''),
            "email_from": summary.get('email', ''),
            "x_lead_score": summary.get('lead_score', 0),
            "x_lead_type": summary.get('lead_type', 'Unqualified'),
            "x_utm_source": summary.get('utm_source', 'direct'),
            "x_session_start_time": summary.get('created_at', ''),
            "user_id": 5,  # Replace with your Odoo user ID
        }
        url = os.getenv("ODOO_URL")
        db = os.getenv("ODOO_DB")
        username = os.getenv("ODOO_USERNAME")
        password = os.getenv("ODOO_PASSWORD")
        user_id = int(os.getenv("ODOO_USER_ID", "5"))
        lead_data["user_id"] = user_id
        try:
            # Connect to Odoo XML-RPC
            common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
            
            # Authenticate
            uid = common.authenticate(db, username, password, {})
            if not uid:
                print("Odoo authentication failed")
                return None
            
            # Create the lead
            models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
            lead_id = models.execute_kw(
                db, uid, password, 'crm.lead', 'create', [lead_data])
            
            print(f"Successfully created lead in Odoo with ID: {lead_id}")
            return lead_id
            
        except Exception as e:
            print(f"Odoo sync failed: {e}")
            return None

    @staticmethod
    def check_all_questions_answered(session_id):
        """Check if all required questions have been answered."""
        db_session = get_db_session()
        try:
            # Get all required questions
            questions = QuestionService.get_questions()
            required_questions = [q['id']
                                  for q in questions if q.get('required', True)]

            # Get answered questions for this session
            answered_questions = db_session.query(Answer.question_id).filter_by(
                session_id=session_id).distinct().all()
            answered_question_ids = [row[0] for row in answered_questions]

            # Check if all required questions are answered
            all_answered = all(
                qid in answered_question_ids for qid in required_questions)

            if all_answered:
                # Award bonus for completing all questions
                ScoringService.log_behavior(
                    session_id, 'answered_all_questions')

            return all_answered
        except Exception as e:
            print(f"Error checking questions completion: {e}")
            return False
        finally:
            db_session.close()


# New: Customer ID Service
class CustomerService:
    @staticmethod
    def generate_customer_id():
        """Generate unique customer ID in format CID_YYYYMMDD_XXXX"""
        db_session = get_db_session()
        try:
            today = date.today().strftime("%Y%m%d")

            # Get the count of customers created today
            today_count = db_session.query(Lead).filter(
                Lead.customer_id.like(f"CID_{today}_%")
            ).count()

            next_number = str(today_count + 1).zfill(4)
            customer_id = f"CID_{today}_{next_number}"

            return customer_id
        except Exception as e:
            print(f"Error generating customer ID: {e}")
            return None
        finally:
            db_session.close()

    @staticmethod
    def assign_customer_id(session_id):
        """Assign customer ID to existing session"""
        db_session = get_db_session()
        try:
            print(f"[DEBUG] Looking for session_id: {session_id}")
            lead = db_session.query(Lead).filter_by(
                session_id=session_id).first()
            print(f"[DEBUG] Found lead: {lead}")

            if lead and not lead.customer_id:
                customer_id = CustomerService.generate_customer_id()
                print(f"[DEBUG] Generated customer_id: {customer_id}")
                lead.customer_id = customer_id
                db_session.add(lead)  # Explicitly add the modified object
                db_session.commit()
                # Refresh to ensure changes are persisted
                db_session.refresh(lead)
                print(
                    f"[DEBUG] Assigned customer_id {customer_id} to session {session_id}")
                return customer_id
            elif lead and lead.customer_id:
                print(
                    f"[DEBUG] Lead already has customer_id: {lead.customer_id}")
                return lead.customer_id
            else:
                print(f"[DEBUG] No lead found for session_id: {session_id}")
                return None
        except Exception as e:
            print(f"Error assigning customer ID: {e}")
            import traceback
            traceback.print_exc()
            db_session.rollback()
            return None
        finally:
            db_session.close()

    @staticmethod
    def get_customer_details(customer_id):
        """Get complete customer details by customer ID"""
        db_session = get_db_session()
        try:
            print(f"[DEBUG] Looking for customer_id: {customer_id}")
            lead = db_session.query(Lead).filter_by(
                customer_id=customer_id).first()
            print(f"[DEBUG] Found lead: {lead}")

            if lead:
                # Get CIF data if available
                cif = db_session.query(CustomerInformationForm).filter_by(
                    customer_id=customer_id
                ).first()
                print(f"[DEBUG] Found CIF: {cif}")

                # Get page tracking data
                pages = db_session.query(PageTracking).filter_by(
                    customer_id=customer_id
                ).order_by(PageTracking.entry_time).all()
                print(f"[DEBUG] Found pages: {len(pages)}")

                # Get behaviors
                behaviors = db_session.query(UserBehavior).filter_by(
                    session_id=lead.session_id
                ).order_by(UserBehavior.created_at).all()
                print(f"[DEBUG] Found behaviors: {len(behaviors)}")

                return {
                    'customer_id': customer_id,
                    'session_id': lead.session_id,
                    'lead_data': {
                        'name': lead.name,
                        'email': lead.email,
                        'phone': lead.phone,
                        'business_type': lead.business_type,
                        'location': lead.location,
                        'lead_score': lead.lead_score,
                        'lead_type': lead.lead_type,
                        'utm_source': lead.utm_source,
                        'cif_completed': lead.cif_completed
                    },
                    'cif_data': cif.form_data if cif else None,
                    'page_journey': [
                        {
                            'page': page.page_identifier,
                            'question_id': page.question_id,
                            'entry_time': page.entry_time.isoformat(),
                            'exit_time': page.exit_time.isoformat() if page.exit_time else None,
                            'time_spent': page.time_spent,
                            'page_type': page.page_type
                        } for page in pages
                    ],
                    'behaviors': [
                        {
                            'action': behavior.action,
                            'score_change': behavior.score_change,
                            'timestamp': behavior.created_at.isoformat()
                        } for behavior in behaviors
                    ]
                }
            print(f"[DEBUG] No lead found for customer_id: {customer_id}")
            return None
        except Exception as e:
            print(f"Error getting customer details: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            db_session.close()


# New: Page Tracking Service
class PageTrackingService:
    @staticmethod
    def get_page_performance_analytics():
        """Aggregate page views, average time spent, and conversion rates per page."""
        db_session = get_db_session()
        try:
            from sqlalchemy import func
            results = db_session.query(
                PageTracking.page_identifier,
                func.count(PageTracking.id).label('views'),
                func.avg(PageTracking.time_spent).label('avg_time')
            ).group_by(PageTracking.page_identifier).all()

            analytics = []
            for row in results:
                analytics.append({
                    'page': row.page_identifier,
                    'views': row.views,
                    'avg_time_spent': float(row.avg_time) if row.avg_time else 0.0
                })
            return {'page_performance': analytics}
        except Exception as e:
            print(f"Error getting page performance analytics: {e}")
            return {'page_performance': []}
        finally:
            db_session.close()

    @staticmethod
    def get_all_customer_journeys():
        """Aggregate journeys for all customers/sessions."""
        db_session = get_db_session()
        try:
            sessions = db_session.query(
                PageTracking.session_id).distinct().all()
            journeys = []
            for session in sessions:
                session_id = session.session_id
                pages = db_session.query(PageTracking).filter_by(
                    session_id=session_id).order_by(PageTracking.entry_time).all()
                journey = [{
                    'page': page.page_identifier,
                    'entry_time': page.entry_time.isoformat(),
                    'exit_time': page.exit_time.isoformat() if page.exit_time else None,
                    'time_spent': page.time_spent
                } for page in pages]
                journeys.append({'session_id': session_id, 'journey': journey})
            return {'customer_journeys': journeys}
        except Exception as e:
            print(f"Error getting all customer journeys: {e}")
            return {'customer_journeys': []}
        finally:
            db_session.close()

    @staticmethod
    def log_page_entry(session_id, page_identifier, question_id=None, page_type=None, metadata=None):
        """Log when user enters a page"""
        db_session = get_db_session()
        try:
            # Get customer ID if available
            lead = db_session.query(Lead).filter_by(
                session_id=session_id).first()
            customer_id = lead.customer_id if lead else None

            page_tracking = PageTracking(
                session_id=session_id,
                customer_id=customer_id,
                page_identifier=page_identifier,
                question_id=question_id,
                page_type=page_type or 'unknown',
                page_metadata=metadata
            )
            db_session.add(page_tracking)
            db_session.commit()
            return page_tracking.id
        except Exception as e:
            print(f"Error logging page entry: {e}")
            db_session.rollback()
            return None
        finally:
            db_session.close()

    @staticmethod
    def log_page_exit(page_tracking_id, exit_time=None):
        """Log when user exits a page"""
        db_session = get_db_session()
        try:
            page_tracking = db_session.query(
                PageTracking).filter_by(id=page_tracking_id).first()
            if page_tracking:
                exit_time = exit_time or datetime.now()
                page_tracking.exit_time = exit_time

                # Calculate time spent
                if page_tracking.entry_time:
                    time_spent = (
                        exit_time - page_tracking.entry_time).total_seconds()
                    page_tracking.time_spent = int(time_spent)

                db_session.commit()
                return True
        except Exception as e:
            print(f"Error logging page exit: {e}")
            db_session.rollback()
            return False
        finally:
            db_session.close()

    @staticmethod
    def get_customer_journey(session_id):
        """Get complete page journey for a session"""
        db_session = get_db_session()
        try:
            pages = db_session.query(PageTracking).filter_by(
                session_id=session_id
            ).order_by(PageTracking.entry_time).all()

            return [
                {
                    'id': page.id,
                    'page': page.page_identifier,
                    'question_id': page.question_id,
                    'page_type': page.page_type,
                    'entry_time': page.entry_time.isoformat(),
                    'exit_time': page.exit_time.isoformat() if page.exit_time else None,
                    'time_spent': page.time_spent,
                    'metadata': page.page_metadata
                } for page in pages
            ]
        except Exception as e:
            print(f"Error getting customer journey: {e}")
            return []
        finally:
            db_session.close()


# New: Customer Information Form Service
class CIFService:
    @staticmethod
    def get_cif_completion_analytics():
        """Aggregate CIF completion rates and breakdowns."""
        db_session = get_db_session()
        try:
            from sqlalchemy import func
            total = db_session.query(func.count(
                CustomerInformationForm.id)).scalar()
            completed = db_session.query(func.count(CustomerInformationForm.id)).filter(
                CustomerInformationForm.completion_percentage >= 100.0).scalar()
            avg_completion = db_session.query(
                func.avg(CustomerInformationForm.completion_percentage)).scalar()
            return {
                'total_cif': total,
                'completed_cif': completed,
                'avg_completion_percentage': float(avg_completion) if avg_completion else 0.0
            }
        except Exception as e:
            print(f"Error getting CIF completion analytics: {e}")
            return {
                'total_cif': 0,
                'completed_cif': 0,
                'avg_completion_percentage': 0.0
            }
        finally:
            db_session.close()

    @staticmethod
    def start_cif(session_id, customer_id):
        """Start CIF process for a customer"""
        db_session = get_db_session()
        try:
            # Check if CIF already exists
            existing_cif = db_session.query(CustomerInformationForm).filter_by(
                customer_id=customer_id
            ).first()

            if not existing_cif:
                cif = CustomerInformationForm(
                    customer_id=customer_id,
                    session_id=session_id,
                    form_data={},
                    completion_percentage=0.0
                )
                db_session.add(cif)
                db_session.commit()
                return cif.id
            return existing_cif.id
        except Exception as e:
            print(f"Error starting CIF: {e}")
            db_session.rollback()
            return None
        finally:
            db_session.close()

    @staticmethod
    def update_cif_data(customer_id, form_data, section=None):
        """Update CIF data for a customer"""
        db_session = get_db_session()
        try:
            cif = db_session.query(CustomerInformationForm).filter_by(
                customer_id=customer_id
            ).first()

            if cif:
                if section:
                    # Update specific section
                    current_data = cif.form_data or {}
                    current_data[section] = form_data
                    cif.form_data = current_data
                else:
                    # Update entire form data
                    cif.form_data = form_data

                # Calculate completion percentage
                completion_percentage = CIFService._calculate_completion_percentage(
                    cif.form_data)
                cif.completion_percentage = completion_percentage

                # Mark as completed if 100%
                if completion_percentage >= 100.0:
                    cif.completed_at = datetime.now()

                    # Update lead table
                    lead = db_session.query(Lead).filter_by(
                        customer_id=customer_id).first()
                    if lead:
                        lead.cif_completed = True

                db_session.commit()
                return True
            return False
        except Exception as e:
            print(f"Error updating CIF data: {e}")
            db_session.rollback()
            return False
        finally:
            db_session.close()

    @staticmethod
    def _calculate_completion_percentage(form_data):
        """Calculate CIF completion percentage"""
        if not form_data:
            return 0.0

        required_sections = [
            'basic_info', 'business_details', 'operational_info',
            'technology_profile', 'financial_info'
        ]

        required_fields = {
            'basic_info': ['full_name', 'email', 'phone'],
            'business_details': ['business_name', 'business_type', 'industry'],
            'operational_info': ['staff_size', 'monthly_sales'],
            'technology_profile': ['current_pos', 'features_needed'],
            'financial_info': ['annual_revenue', 'investment_capacity']
        }

        total_fields = sum(len(fields) for fields in required_fields.values())
        completed_fields = 0

        for section, fields in required_fields.items():
            if section in form_data:
                for field in fields:
                    if field in form_data[section] and form_data[section][field]:
                        completed_fields += 1

        return (completed_fields / total_fields) * 100.0

    @staticmethod
    def get_cif_data(customer_id):
        """Get CIF data for a customer"""
        db_session = get_db_session()
        try:
            cif = db_session.query(CustomerInformationForm).filter_by(
                customer_id=customer_id
            ).first()

            if cif:
                return {
                    'customer_id': cif.customer_id,
                    'session_id': cif.session_id,
                    'form_data': cif.form_data,
                    'completion_percentage': cif.completion_percentage,
                    'completed_at': cif.completed_at.isoformat() if cif.completed_at else None,
                    'created_at': cif.created_at.isoformat(),
                    'updated_at': cif.updated_at.isoformat()
                }
            return None
        except Exception as e:
            print(f"Error getting CIF data: {e}")
            return None
        finally:
            db_session.close()


# New: Session Exit Service
class SessionExitService:
    @staticmethod
    def log_session_exit(session_id, exit_reason='abandoned', exit_question_id=None,
                         exit_page=None, last_action=None, metadata=None):
        """Log when a session exits/ends"""
        db_session = get_db_session()
        try:
            # Get customer ID if available
            lead = db_session.query(Lead).filter_by(
                session_id=session_id).first()
            customer_id = lead.customer_id if lead else None

            # Calculate completion percentage
            completion_percentage = SessionExitService._calculate_session_completion(
                session_id)

            session_exit = SessionExit(
                session_id=session_id,
                customer_id=customer_id,
                exit_question_id=exit_question_id,
                exit_page=exit_page,
                exit_reason=exit_reason,
                session_completion_percentage=completion_percentage,
                last_action=last_action,
                exit_metadata=metadata
            )
            db_session.add(session_exit)
            db_session.commit()
            return session_exit.id
        except Exception as e:
            print(f"Error logging session exit: {e}")
            db_session.rollback()
            return None
        finally:
            db_session.close()

    @staticmethod
    def _calculate_session_completion(session_id):
        """Calculate what percentage of the session was completed"""
        db_session = get_db_session()
        try:
            # Get total required questions
            questions = QuestionService.get_questions()
            required_questions = [q['id']
                                  for q in questions if q.get('required', True)]
            total_required = len(required_questions)

            # Get answered questions
            answered_count = db_session.query(Answer).filter_by(
                session_id=session_id
            ).distinct(Answer.question_id).count()

            if total_required == 0:
                return 100.0

            return (answered_count / total_required) * 100.0
        except Exception as e:
            print(f"Error calculating session completion: {e}")
            return 0.0
        finally:
            db_session.close()

    @staticmethod
    def get_abandonment_analytics():
        """Get analytics on where users typically abandon sessions"""
        db_session = get_db_session()
        try:
            # Get most common exit points
            exit_points = db_session.query(
                SessionExit.exit_question_id,
                SessionExit.exit_page,
                db_session.query(SessionExit).filter_by(
                    exit_question_id=SessionExit.exit_question_id,
                    exit_page=SessionExit.exit_page
                ).count().label('count')
            ).group_by(SessionExit.exit_question_id, SessionExit.exit_page).all()

            # Get average completion percentage by exit reason
            completion_by_reason = db_session.query(
                SessionExit.exit_reason,
                db_session.query(SessionExit.session_completion_percentage).filter_by(
                    exit_reason=SessionExit.exit_reason
                ).func.avg().label('avg_completion')
            ).group_by(SessionExit.exit_reason).all()

            return {
                'common_exit_points': [
                    {
                        'question_id': point.exit_question_id,
                        'page': point.exit_page,
                        'count': point.count
                    } for point in exit_points
                ],
                'completion_by_reason': [
                    {
                        'reason': reason.exit_reason,
                        'avg_completion': float(reason.avg_completion) if reason.avg_completion else 0.0
                    } for reason in completion_by_reason
                ]
            }
        except Exception as e:
            print(f"Error getting abandonment analytics: {e}")
            return {'common_exit_points': [], 'completion_by_reason': []}
        finally:
            db_session.close()
