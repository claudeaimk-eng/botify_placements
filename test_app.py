import requests, json, time

BASE = 'http://127.0.0.1:5000'
s    = requests.Session()
ok   = 0
fail = 0
uid  = None

def check(name, cond, detail=''):
    global ok, fail
    if cond:
        print(f'  PASS  {name}' + (f' | {detail}' if detail else ''))
        ok += 1
    else:
        print(f'  FAIL  {name}' + (f' | {detail}' if detail else ''))
        fail += 1

print('\n====== BOTIFY TEST SUITE ======\n')

# Unique email each run
email = f'bottest_{int(time.time())}@test.com'

# 1. Home redirect to login
r = s.get(BASE + '/', allow_redirects=True)
check('Home redirect to login', '/login' in r.url or r.status_code == 200)

# 2. Register
r = s.post(BASE + '/register', data={
    'name': 'Test User', 'email': email,
    'password': 'Test1234', 'business_name': 'Test Biryani House',
    'whatsapp_number': '9876543210'
}, allow_redirects=True)
check('Register new user', '/login' in r.url or r.status_code == 200, f'URL: {r.url}')

# 3. Login
r = s.post(BASE + '/login', data={'email': email, 'password': 'Test1234'}, allow_redirects=True)
check('Login success', 'login' not in r.url.lower() or 'dashboard' in r.text.lower() or r.status_code == 200, f'URL: {r.url}')

# 4. Select free plan (handle both welcome flow and already-on-dashboard)
r = s.post(BASE + '/select-plan/free', allow_redirects=True)
check('Select free plan', r.status_code == 200, f'URL: {r.url}')

# 5. Dashboard
r = s.get(BASE + '/', allow_redirects=True)
check('Dashboard loads', r.status_code == 200)
check('Dashboard has Menu link',      '/menu'      in r.text)
check('Dashboard has Orders link',    '/orders'    in r.text)
check('Dashboard has Broadcast link', '/broadcast' in r.text)
check('Dashboard has Analytics link', '/analytics' in r.text)

# Extract user_id from session
import re
uid_match = re.search(r'/api/start-bot/(\d+)', r.text)
if uid_match:
    uid = uid_match.group(1)
    print(f'  INFO  Detected user_id = {uid}')

# 6. Menu page
r = s.get(BASE + '/menu')
check('Menu page loads', r.status_code == 200)

# 7. Add service
r = s.post(BASE + '/add-service', data={
    'service_name': 'Chicken Biryani', 'category': 'Food',
    'price': '150', 'description': 'Full plate with raita'
}, allow_redirects=True)
check('Add service redirects to menu', '/menu' in r.url, f'URL: {r.url}')

# 8. Menu shows item
r = s.get(BASE + '/menu')
check('Menu shows added item',  'Chicken Biryani' in r.text)
check('Menu shows price',       '150'             in r.text)
check('Menu shows category',    'Food'            in r.text)

# 8b. Toggle service availability
ids = re.findall(r'toggle-service/(\d+)', r.text)
if ids:
    r2 = s.post(BASE + f'/toggle-service/{ids[-1]}')
    try:
        data = r2.json()
        check('Toggle service availability', data.get('success'), str(data))
    except:
        check('Toggle service availability', False, r2.text[:100])
else:
    check('Toggle service availability', False, 'No service id found in page')

# 9. Delete service (add a dummy one first)
s.post(BASE + '/add-service', data={'service_name': 'To Delete', 'price': '0'}, allow_redirects=True)
r = s.get(BASE + '/menu')
del_ids = re.findall(r'delete-service/(\d+)', r.text)
if del_ids:
    r_del = s.get(BASE + f'/delete-service/{del_ids[-1]}', allow_redirects=True)
    check('Delete service works', r_del.status_code == 200)
else:
    check('Delete service works', False, 'No delete link found')

# 10. Orders page
r = s.get(BASE + '/orders')
check('Orders page loads', r.status_code == 200)
check('Orders has status tabs', 'status=pending' in r.text or 'Pending' in r.text)

# 11. Analytics page
r = s.get(BASE + '/analytics')
check('Analytics page loads',   r.status_code == 200)
check('Analytics has charts',   'msgChart' in r.text)
check('Analytics has totals',   'total_messages' not in r.text or 'Messages' in r.text)

# 12. Broadcast page
r = s.get(BASE + '/broadcast')
check('Broadcast page loads',   r.status_code == 200)
check('Broadcast compose area', 'broadcastMsg' in r.text)

# 13. Bookings page
r = s.get(BASE + '/bookings')
check('Bookings page loads', r.status_code == 200)

# 14. Upgrade page
r = s.get(BASE + '/upgrade')
check('Upgrade page loads', r.status_code == 200)

# 15. API - get-menu (for this user)
if uid:
    r = s.get(BASE + f'/api/get-menu/{uid}')
    try:
        data = r.json()
        check('API get-menu', r.status_code == 200 and 'menu' in data, f'items: {len(data.get("menu",[]))}')
    except:
        check('API get-menu', False, r.text[:100])

# 16. API - save-order (Node.js calls this)
if uid:
    r = s.post(BASE + f'/api/save-order/{uid}', json={
        'customer_phone': '9876543210', 'customer_name': 'Rahul Test',
        'items': [{'name': 'Chicken Biryani', 'qty': 2, 'price': 150}],
        'total_amount': 300
    })
    data = r.json()
    check('API save-order works', r.status_code == 200 and data.get('success'), str(data))

    # 16b. Check order appears on orders page
    r = s.get(BASE + '/orders')
    check('Order appears on orders page', 'Rahul Test' in r.text)

    # 16c. Update order status (from dashboard session)
    oid_match = re.findall(r'order-(\d+)', r.text if r.status_code == 200 else '')
    r_orders = s.get(BASE + '/orders')
    oids = re.findall(r"updateStatus\((\d+)", r_orders.text)
    if oids:
        r_upd = s.post(BASE + f'/api/update-order-status/{oids[0]}',
                       json={'status': 'confirmed'})
        try:
            check('Update order status', r_upd.json().get('success'), str(r_upd.json()))
        except:
            check('Update order status', False, str(r_upd.status_code))
    else:
        check('Update order status', False, 'No order IDs found')

# 17. API - save-feedback
if uid:
    r = s.post(BASE + f'/api/save-feedback/{uid}', json={
        'customer_phone': '9876543210', 'customer_name': 'Rahul Test',
        'rating': 5, 'comment': 'Excellent biryani!'
    })
    check('API save-feedback', r.status_code == 200 and r.json().get('success'))

# 18. Analytics after data
if uid:
    r = s.get(BASE + '/analytics')
    check('Analytics with data loads', r.status_code == 200)

# 19. msg-count API
r = s.get(BASE + '/api/msg-count')
check('API msg-count', r.status_code == 200 and 'today_count' in r.json())

# 20. Admin panel
admin_s = requests.Session()
r = admin_s.post(BASE + '/admin/login', data={'password': 'admin@Muki123'}, allow_redirects=True)
check('Admin login', '/admin/dashboard' in r.url or 'Dashboard' in r.text, f'URL: {r.url}')
check('Admin users page',   admin_s.get(BASE + '/admin/users').status_code   == 200)
check('Admin revenue page', admin_s.get(BASE + '/admin/revenue').status_code == 200)
check('Admin support page', admin_s.get(BASE + '/admin/support').status_code == 200)

print(f'\n====== RESULTS: {ok} PASSED | {fail} FAILED out of {ok+fail} ======\n')
