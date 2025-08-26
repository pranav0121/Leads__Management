import os
import xmlrpc.client
from dotenv import load_dotenv

load_dotenv()

def test_odoo_sync():
    url = os.getenv("ODOO_URL")
    db = os.getenv("ODOO_DB")
    username = os.getenv("ODOO_USERNAME")
    password = os.getenv("ODOO_PASSWORD")

    try:
        print(f"Testing connection to: {url}")
        print(f"Database: {db}")
        print(f"Username: {username}")

        # Connect to Odoo XML-RPC
        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")

        # Authenticate
        uid = common.authenticate(db, username, password, {})
        if not uid:
            print("Authentication failed")
            return

        print(f"Authentication successful. User ID: {uid}")

        # Test lead creation
        models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
        lead_data = {
            "name": "Test Lead",
            "type": "opportunity",
            "email_from": "test@example.com",
            "phone": "1234567890",
        }
        lead_id = models.execute_kw(
            db, uid, password, 'crm.lead', 'create', [lead_data]
        )
        print(f"Lead created successfully with ID: {lead_id}")

    except Exception as e:
        print(f"Odoo sync failed: {e}")

if __name__ == "__main__":
    test_odoo_sync()
