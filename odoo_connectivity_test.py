import os
import xmlrpc.client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("ODOO_URL")
db = os.getenv("ODOO_DB")
username = os.getenv("ODOO_USERNAME")
password = os.getenv("ODOO_PASSWORD")

print(f"Testing Odoo connection to: {url}")
print(f"Database: {db}")
print(f"Username: {username}")

try:
    # Test connection to common endpoint
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    version = common.version()
    print(f"Odoo version: {version}")

    # Test authentication
    uid = common.authenticate(db, username, password, {})
    print(f"Authentication result: {uid}")
    if not uid:
        print("Odoo authentication failed. Check credentials and database name.")
    else:
        print("Odoo authentication successful.")

        # Test models access
        models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
        # Try to read crm.lead model (just check access)
        try:
            leads = models.execute_kw(db, uid, password, 'crm.lead', 'search', [[]], {'limit': 1})
            print(f"crm.lead search result: {leads}")
        except Exception as e:
            print(f"Error accessing crm.lead: {e}")
except Exception as e:
    print(f"Odoo connectivity test failed: {e}")
