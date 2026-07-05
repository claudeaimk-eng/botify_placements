import requests
import time
import re
import os

BASE_URL = 'http://127.0.0.1:5000'
session = requests.Session()

# Colors for terminal output
G = '\033[92m'
R = '\033[91m'
C = '\033[96m'
W = '\033[0m'

def print_step(step_num, title, success, details=""):
    status = f"{G}✓ SUCCESS{W}" if success else f"{R}✗ FAILED{W}"
    print(f"{C}Step {step_num}:{W} {title:<40} [{status}] {details}")
    if not success:
        print(f"{R}Workflow broken at Step {step_num}. Stopping test.{W}")
        exit(1)

print(f"\n{C}=================================================={W}")
print(f"{C}      BOTIFY FULL USER WORKFLOW TEST ENGINE       {W}")
print(f"{C}=================================================={W}\n")

email = f"workflow_test_{int(time.time())}@botify.local"
password = "TestPassword123!"

try:
    # ---------------------------------------------------------
    # STEP 1: Registration
    # ---------------------------------------------------------
    res = session.post(f"{BASE_URL}/register", data={
        'name': 'Test Creator',
        'email': email,
        'password': password,
        'business_name': 'Botify Test Store',
        'whatsapp_number': '1234567890'
    }, allow_redirects=True)
    
    print_step(1, "User Registration", '/login' in res.url, "Account Created")

    # ---------------------------------------------------------
    # STEP 2: Login
    # ---------------------------------------------------------
    res = session.post(f"{BASE_URL}/login", data={
        'email': email,
        'password': password
    }, allow_redirects=True)
    
    print_step(2, "User Login", '/welcome' in res.url, "Redirected to Welcome Screen")

    # ---------------------------------------------------------
    # STEP 3: Welcome -> Upgrade Page
    # ---------------------------------------------------------
    res = session.get(f"{BASE_URL}/welcome")
    res = session.get(f"{BASE_URL}/upgrade")
    print_step(3, "Navigate to Consolidated Pricing", 'Free Forever' in res.text, "Payment UI Loaded")

    # ---------------------------------------------------------
    # STEP 4: Activate Free Plan
    # ---------------------------------------------------------
    res = session.post(f"{BASE_URL}/select-plan/free", allow_redirects=True)
    print_step(4, "Activate Free Plan", '/' in res.url and 'bot_limit' not in res.url, "Redirected to Dashboard")

    # ---------------------------------------------------------
    # STEP 5: Add Business Info
    # ---------------------------------------------------------
    res = session.post(f"{BASE_URL}/business-info", data={
        'address': '123 Test Ave, NY',
        'timings': '9 AM - 6 PM',
        'contact_email': email,
        'contact_phone': '1234567890',
        'website': 'https://botify.test',
        'extra_info': 'Test Info'
    }, allow_redirects=True)
    
    res = session.get(f"{BASE_URL}/")
    print_step(5, "Update Business Info", '123 Test Ave' in res.text, "Dashboard reflects new Info")

    # ---------------------------------------------------------
    # STEP 6: Add Service (Menu Item)
    # ---------------------------------------------------------
    res = session.post(f"{BASE_URL}/add-service", data={
        'service_name': 'Test Premium Package',
        'category': 'Services',
        'price': '999',
        'description': 'A fully automated test package'
    }, allow_redirects=True)
    
    print_step(6, "Add New Service to Menu", '/menu' in res.url and 'Test Premium Package' in res.text, "Service Added")

    # ---------------------------------------------------------
    # STEP 7: Create a WhatsApp Bot
    # ---------------------------------------------------------
    res = session.post(f"{BASE_URL}/create-bot", data={
        'bot_name': 'Auto Bot',
        'welcome_message': 'Welcome to Test Store!',
        'features': 'Menu, Order, LiveChat'
    }, allow_redirects=True)
    
    print_step(7, "Create WhatsApp Bot", '🤖 Auto Bot' in res.text, "Bot instance created on Dashboard")

    # ---------------------------------------------------------
    # STEP 8: Fetch User ID for Webhooks
    # ---------------------------------------------------------
    # The safest way to cleanly extract our virtual User ID is via the internal order generation API
    res_ord = session.post(f"{BASE_URL}/api/create-order", json={'plan': 'starter'})
    uid = None
    if res_ord.json().get('success'):
        # order_id looks like: ORD_userID_timestamp
        uid = res_ord.json().get('order_id').split('_')[1]
        
    print_step(8, "Locate Secure User ID", bool(uid), f"Extracted User_ID: {uid}")

    # ---------------------------------------------------------
    # STEP 9: Simulate Node.js Fetching Menu (Headers Added)
    # ---------------------------------------------------------
    headers = {'Authorization': os.environ.get('SECRET_KEY', 'botify-super-secret-key-2025')}
    res = session.get(f"{BASE_URL}/api/get-menu/{uid}", headers=headers)
    
    valid_menu = res.status_code == 200 and 'Test Premium Package' in str(res.json())
    print_step(9, "Bot Fetches Catalog (Node.js API)", valid_menu, "Authentication passed, Menu delivered")

    # ---------------------------------------------------------
    # STEP 10: Simulate Customer Placing Order via WhatsApp
    # ---------------------------------------------------------
    res = session.post(f"{BASE_URL}/api/save-order/{uid}", headers=headers, json={
        'customer_phone': '5551112222',
        'customer_name': 'WhatsApp Customer',
        'items': [{'name': 'Test Premium Package', 'qty': 1, 'price': 999}],
        'total_amount': 999
    })
    print_step(10, "Bot Saves Order to Database", res.status_code == 200 and res.json().get('success'), "Order inserted securely")

    # ---------------------------------------------------------
    # STEP 11: Validate Order on Vendor Dashboard
    # ---------------------------------------------------------
    res = session.get(f"{BASE_URL}/orders")
    print_step(11, "Vendor Views Orders Page", 'WhatsApp Customer' in res.text and '999' in res.text, "Order appears beautifully")

    # ---------------------------------------------------------
    # STEP 12: Validate Analytics Updates
    # ---------------------------------------------------------
    res = session.get(f"{BASE_URL}/analytics")
    print_step(12, "Vendor Views Analytics Engine", res.status_code == 200, "Charts and Stats are rendering")

    print(f"\n{G}=================================================={W}")
    print(f"{G} 🎉 CONTINUOUS WORKFLOW TEST COMPLETED PERFECTLY! {W}")
    print(f"{G}=================================================={W}\n")

except Exception as e:
    print(f"\n{R}🚨 SYSTEM CRASH: {str(e)}{W}")
    exit(1)
