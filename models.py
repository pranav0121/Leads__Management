from sqlalchemy import Column, String, Integer, Float, Text, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from database import Base


class Question(Base):
    __tablename__ = 'questions'

    id = Column(Integer, primary_key=True)
    text = Column(String, nullable=False)
    score = Column(Float, nullable=False)


class Answer(Base):
    __tablename__ = 'answers'

    id = Column(Integer, primary_key=True)
    session_id = Column(String, nullable=False)
    question_id = Column(Integer, nullable=False)
    answer_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())


class Lead(Base):
    __tablename__ = 'leads'

    id = Column(Integer, primary_key=True)
    session_id = Column(String, nullable=False, unique=True)
    customer_id = Column(String(50), nullable=True,
                         unique=True)  # New: CID tracking
    utm_source = Column(String, nullable=True)
    lead_score = Column(Float, default=0.0)
    lead_type = Column(String, nullable=True)  # SQL, MQL, Unqualified
    name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    business_type = Column(String, nullable=True)
    location = Column(String, nullable=True)
    staff_size = Column(String, nullable=True)
    monthly_sales = Column(String, nullable=True)
    features_interested = Column(Text, nullable=True)  # JSON string
    # New: CIF completion status
    cif_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class UserBehavior(Base):
    __tablename__ = 'user_behaviors'

    id = Column(Integer, primary_key=True)
    session_id = Column(String, nullable=False)
    action = Column(String, nullable=False)
    score_change = Column(Float, default=0.0)
    behavior_metadata = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, default=func.now())


# New: Customer Information Form
class CustomerInformationForm(Base):
    __tablename__ = 'customer_information_forms'

    id = Column(Integer, primary_key=True)
    customer_id = Column(String(50), nullable=False, unique=True)
    session_id = Column(String, nullable=False)
    form_data = Column(JSON, nullable=True)  # Complete CIF data
    completed_at = Column(DateTime, nullable=True)
    completion_percentage = Column(Float, default=0.0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


# New: Page-by-page tracking
class PageTracking(Base):
    __tablename__ = 'page_tracking'

    id = Column(Integer, primary_key=True)
    session_id = Column(String, nullable=False)
    customer_id = Column(String(50), nullable=True)
    page_identifier = Column(String(100), nullable=False)
    question_id = Column(Integer, nullable=True)
    entry_time = Column(DateTime, default=func.now())
    exit_time = Column(DateTime, nullable=True)
    time_spent = Column(Integer, nullable=True)  # seconds
    # 'question', 'form', 'summary', etc.
    page_type = Column(String(50), nullable=True)
    # Additional tracking data (renamed from metadata)
    page_metadata = Column(JSON, nullable=True)


# New: Session exit tracking
class SessionExit(Base):
    __tablename__ = 'session_exits'

    id = Column(Integer, primary_key=True)
    session_id = Column(String, nullable=False)
    customer_id = Column(String(50), nullable=True)
    exit_question_id = Column(Integer, nullable=True)
    exit_page = Column(String(100), nullable=True)
    # 'completed', 'abandoned', 'timeout'
    exit_reason = Column(String(50), nullable=True)
    exit_time = Column(DateTime, default=func.now())
    session_completion_percentage = Column(Float, nullable=True)
    last_action = Column(String(100), nullable=True)
    exit_metadata = Column(JSON, nullable=True)  # Renamed from metadata
