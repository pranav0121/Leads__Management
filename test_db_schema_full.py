import pytest
from sqlalchemy import inspect
from database import engine

table_columns = {
    'leads': [
        'id', 'session_id', 'customer_id', 'utm_source', 'lead_score', 'lead_type',
        'name', 'email', 'phone', 'business_type', 'location', 'staff_size',
        'monthly_sales', 'features_interested', 'cif_completed', 'created_at', 'updated_at'
    ],
    'answers': [
        'id', 'session_id', 'question_id', 'answer_text', 'created_at'
    ],
    'questions': [
        'id', 'text', 'score'
    ],
    'user_behaviors': [
        'id', 'session_id', 'action', 'score_change', 'behavior_metadata', 'created_at'
    ],
    'customer_information_forms': [
        'id', 'customer_id', 'session_id', 'form_data', 'completed_at', 'completion_percentage', 'created_at', 'updated_at'
    ],
    'page_tracking': [
        'id', 'session_id', 'customer_id', 'page_identifier', 'question_id', 'entry_time', 'exit_time', 'time_spent', 'page_type', 'page_metadata'
    ],
    'session_exits': [
        'id', 'session_id', 'customer_id', 'exit_question_id', 'exit_page', 'exit_reason', 'exit_time', 'session_completion_percentage', 'last_action', 'exit_metadata'
    ]
}

def test_all_tables_and_columns_exist():
    inspector = inspect(engine)
    actual_tables = inspector.get_table_names()
    for table, expected_columns in table_columns.items():
        assert table in actual_tables, f"Table '{table}' does not exist."
        columns = [col['name'] for col in inspector.get_columns(table)]
        for col in expected_columns:
            assert col in columns, f"Column '{col}' missing in table '{table}'."

# Optionally, add more tests for indexes, foreign keys, and row counts
