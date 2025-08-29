import pytest
from sqlalchemy import inspect
from database import engine

def test_database_tables_exist():
    inspector = inspect(engine)
    expected_tables = [
        'leads',
        'answers',
        'questions',
        'user_behaviors',
        'customer_information_forms',
        'page_tracking',
        'session_exits'
    ]
    actual_tables = inspector.get_table_names()
    for table in expected_tables:
        assert table in actual_tables, f"Table '{table}' does not exist in the database."


def test_lead_table_columns():
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('leads')]
    expected_columns = [
        'id', 'session_id', 'customer_id', 'utm_source', 'lead_score', 'lead_type',
        'name', 'email', 'phone', 'business_type', 'location', 'staff_size',
        'monthly_sales', 'features_interested', 'cif_completed', 'created_at', 'updated_at'
    ]
    for col in expected_columns:
        assert col in columns, f"Column '{col}' missing in 'leads' table."

# Add similar column tests for other tables as needed
