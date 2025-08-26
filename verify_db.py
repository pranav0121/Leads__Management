import psycopg2
from psycopg2 import sql

def verify_lead_data():
    try:
        # Connect to PostgreSQL database
        connection = psycopg2.connect(
            dbname="leads_management",
            user="postgres",
            password="pranav",
            host="localhost",
            port="5433"
        )
        cursor = connection.cursor()

        # Query to fetch lead data
        query = sql.SQL("SELECT * FROM lead;")
        cursor.execute(query)
        rows = cursor.fetchall()

        # Print fetched data
        print("Lead Data:")
        for row in rows:
            print(row)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

if __name__ == "__main__":
    verify_lead_data()
