#!/usr/bin/env python3
"""
Database migration script to update the answers table structure
to only include session_id, answer_text, and created_at columns
"""

from database import get_db_session, engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_answers_table():
    """
    Migrate the answers table to the new simplified structure
    """
    db_session = get_db_session()

    try:
        logger.info("Starting answers table migration...")

        # First, create a backup of existing data (optional)
        logger.info("Creating backup of existing answers...")
        db_session.execute(text("""
            CREATE TABLE IF NOT EXISTS answers_backup AS 
            SELECT * FROM answers;
        """))

        # Drop the existing answers table
        logger.info("Dropping existing answers table...")
        db_session.execute(text("DROP TABLE IF EXISTS answers CASCADE;"))

        # Create the new simplified answers table
        logger.info("Creating new simplified answers table...")
        db_session.execute(text("""
            CREATE TABLE answers (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR NOT NULL,
                answer_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))

        # Create index for better performance
        db_session.execute(text("""
            CREATE INDEX idx_answers_session_id ON answers(session_id);
        """))

        db_session.commit()
        logger.info("Migration completed successfully!")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db_session.rollback()
        raise
    finally:
        db_session.close()


if __name__ == "__main__":
    migrate_answers_table()
