#!/usr/bin/env python3
"""
Test Odoo connection directly
"""
import xmlrpc.client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_odoo_connection():
    """Test basic Odoo connection and authentication"""
    try:
        url = os.getenv("ODOO_URL")
        db = os.getenv("ODOO_DB")
        username = os.getenv("ODOO_USERNAME")
        password = os.getenv("ODOO_PASSWORD")
        
        print(f"Testing connection to: {url}")
        print(f"Database: {db}")
        print(f"Username: {username}")
        
        # Test connection to common endpoint
        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
        
        # Test version (no auth required)
        version = common.version()
        print(f"Odoo version: {version}")
        
        # Test authentication
        uid = common.authenticate(db, username, password, {})
        print(f"Authentication successful. User ID: {uid}")
        
        if uid:
            # Test models access
            models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
            
            # Try to read crm.lead model (just check access)
            result = models.execute_kw(
                db, uid, password, 'crm.lead', 'search_count', [[]]
            )
            print(f"CRM leads count: {result}")
            
            return True
            
    except Exception as e:
        print(f"Odoo connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_odoo_connection()
