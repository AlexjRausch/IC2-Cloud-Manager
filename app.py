#!/usr/bin/env python3
"""
Peplink InControl2 Manager
A web-based dashboard for monitoring Peplink devices via the InControl2 API.
"""

import http.server
import socketserver
import requests
import json
import os
import hashlib
import secrets
import base64
from urllib.parse import urlparse, parse_qs
from http.cookies import SimpleCookie
from pathlib import Path
from cryptography.fernet import Fernet

CONFIG = {
    'client_id': os.environ.get('PEPLINK_CLIENT_ID', '1c7314d2ecc9c04138e5c7f0d1b538c9'),
    'client_secret': os.environ.get('PEPLINK_CLIENT_SECRET', '75fb1e2a82fa9ef06380a760d8b96b0e'),
    'api_url': os.environ.get('PEPLINK_API_URL', 'https://api.ic.peplink.com'),
    'port': int(os.environ.get('PORT', 8000)),
    'sso_enabled': os.environ.get('SSO_ENABLED', 'false').lower() == 'true',
}

DEFAULT_USERS = {'alex': 'hyrox'}

# Encryption key management
ENCRYPTION_KEY_FILE = Path(__file__).parent / '.encryption_key'
USERS_DB_FILE = Path(__file__).parent / '.users_db.json'
LOCKED_GROUPS_FILE = Path(__file__).parent / '.locked_groups.json'

def get_or_create_encryption_key():
    """Get existing encryption key or create a new one"""
    if ENCRYPTION_KEY_FILE.exists():
        return ENCRYPTION_KEY_FILE.read_bytes()
    key = Fernet.generate_key()
    ENCRYPTION_KEY_FILE.write_bytes(key)
    ENCRYPTION_KEY_FILE.chmod(0o600)  # Secure permissions
    return key

ENCRYPTION_KEY = get_or_create_encryption_key()
cipher = Fernet(ENCRYPTION_KEY)

def encrypt_password(password):
    """Encrypt password using Fernet"""
    return cipher.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password):
    """Decrypt password using Fernet"""
    try:
        return cipher.decrypt(encrypted_password.encode()).decode()
    except:
        return None

def load_users_from_db():
    """Load users from encrypted database file"""
    if USERS_DB_FILE.exists():
        try:
            data = json.loads(USERS_DB_FILE.read_text())
            return data
        except:
            pass
    # Initialize with default users
    default_db = {}
    for username, password in DEFAULT_USERS.items():
        default_db[username] = {
            'password': encrypt_password(password),
            'role': 'admin'
        }
    save_users_to_db(default_db)
    return default_db

def save_users_to_db(users_db):
    """Save users to encrypted database file"""
    USERS_DB_FILE.write_text(json.dumps(users_db, indent=2))
    USERS_DB_FILE.chmod(0o600)

def verify_user_password(username, password):
    """Verify username and password"""
    users_db = load_users_from_db()
    if username not in users_db:
        return False
    encrypted_pwd = users_db[username]['password']
    decrypted_pwd = decrypt_password(encrypted_pwd)
    return decrypted_pwd == password if decrypted_pwd else False

def load_locked_groups():
    """Load locked groups from file"""
    if LOCKED_GROUPS_FILE.exists():
        try:
            return json.loads(LOCKED_GROUPS_FILE.read_text())
        except:
            pass
    return {}

def save_locked_groups(locked_groups):
    """Save locked groups to file"""
    LOCKED_GROUPS_FILE.write_text(json.dumps(locked_groups, indent=2))

locked_groups = load_locked_groups()
USERS = load_users_from_db()

class PeplinkAPI:
    def __init__(self, client_id, client_secret, api_url):
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_url = api_url
        self.access_token = None
    
    def authenticate(self):
        try:
            response = requests.post(
                f"{self.api_url}/api/oauth2/token",
                data={'client_id': self.client_id, 'client_secret': self.client_secret, 'grant_type': 'client_credentials'},
                timeout=30
            )
            if response.status_code == 200:
                self.access_token = response.json().get('access_token')
                print(f'[API] Authenticated successfully')
                return True
            print(f'[API] Authentication failed: {response.status_code}')
        except Exception as e:
            print(f'[API] Authentication error: {e}')
        return False
    
    def get(self, endpoint):
        if not self.access_token:
            self.authenticate()
        if not self.access_token:
            return None
        try:
            response = requests.get(f"{self.api_url}{endpoint}", params={'access_token': self.access_token}, timeout=30)
            if response.status_code == 401:
                if self.authenticate():
                    response = requests.get(f"{self.api_url}{endpoint}", params={'access_token': self.access_token}, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return data.get('data', data) if isinstance(data, dict) else data
        except Exception as e:
            print(f'[API] Request error: {e}')
        return None

    def post(self, endpoint, data=None):
        """POST request to IC2 API"""
        if not self.access_token:
            self.authenticate()
        if not self.access_token:
            return None
        try:
            response = requests.post(
                f"{self.api_url}{endpoint}",
                params={'access_token': self.access_token},
                json=data,
                timeout=30
            )
            if response.status_code == 401:
                if self.authenticate():
                    response = requests.post(
                        f"{self.api_url}{endpoint}",
                        params={'access_token': self.access_token},
                        json=data,
                        timeout=30
                    )
            if response.status_code in [200, 201]:
                return response.json() if response.text else {'success': True}
            print(f'[API] POST failed: {response.status_code} - {response.text}')
        except Exception as e:
            print(f'[API] POST error: {e}')
        return None

    def put(self, endpoint, data=None):
        """PUT request to IC2 API"""
        if not self.access_token:
            self.authenticate()
        if not self.access_token:
            return None
        try:
            response = requests.put(
                f"{self.api_url}{endpoint}",
                params={'access_token': self.access_token},
                json=data,
                timeout=30
            )
            if response.status_code == 401:
                if self.authenticate():
                    response = requests.put(
                        f"{self.api_url}{endpoint}",
                        params={'access_token': self.access_token},
                        json=data,
                        timeout=30
                    )
            if response.status_code in [200, 204]:
                return response.json() if response.text else {'success': True}
            print(f'[API] PUT failed: {response.status_code} - {response.text}')
        except Exception as e:
            print(f'[API] PUT error: {e}')
        return None

    def delete(self, endpoint):
        """DELETE request to IC2 API"""
        if not self.access_token:
            self.authenticate()
        if not self.access_token:
            return None
        try:
            response = requests.delete(
                f"{self.api_url}{endpoint}",
                params={'access_token': self.access_token},
                timeout=30
            )
            if response.status_code == 401:
                if self.authenticate():
                    response = requests.delete(
                        f"{self.api_url}{endpoint}",
                        params={'access_token': self.access_token},
                        timeout=30
                    )
            if response.status_code in [200, 204]:
                return {'success': True}
            print(f'[API] DELETE failed: {response.status_code} - {response.text}')
        except Exception as e:
            print(f'[API] DELETE error: {e}')
        return None

api = PeplinkAPI(CONFIG['client_id'], CONFIG['client_secret'], CONFIG['api_url'])
sessions = {}

def create_session(username):
    session_id = secrets.token_hex(32)
    sessions[session_id] = {'username': username}
    return session_id

def verify_session(cookie_header, headers=None):
    # Check for SSO authentication via Authentik forward auth headers
    if CONFIG['sso_enabled'] and headers:
        authentik_user = headers.get('X-authentik-username') or headers.get('X-Authentik-Username')
        if authentik_user:
            print(f'[SSO] Authenticated user via Authentik: {authentik_user}')
            return True

    # Fallback to session-based authentication
    if not cookie_header:
        return False
    cookie = SimpleCookie()
    cookie.load(cookie_header)
    if 'session_id' in cookie:
        return cookie['session_id'].value in sessions
    return False

def destroy_session(cookie_header):
    if cookie_header:
        cookie = SimpleCookie()
        cookie.load(cookie_header)
        if 'session_id' in cookie:
            sessions.pop(cookie['session_id'].value, None)

LOGIN_PAGE = '''<!DOCTYPE html><html><head><title>Peplink Manager - Login</title><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><style>*{box-sizing:border-box;margin:0;padding:0}body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#1a1a2e;color:#eee;min-height:100vh;display:flex;align-items:center;justify-content:center}.login-container{background:#16213e;padding:40px;border-radius:16px;box-shadow:0 20px 60px rgba(0,0,0,0.5);width:100%;max-width:400px;margin:20px}.login-header{text-align:center;margin-bottom:30px}.login-header h1{font-size:24px;margin-bottom:8px;color:#FF9800}.login-header p{color:#888;font-size:14px}.login-icon{font-size:48px;margin-bottom:15px}.form-group{margin-bottom:20px}.form-group label{display:block;margin-bottom:8px;font-size:12px;color:#888;text-transform:uppercase;letter-spacing:1px}.form-group input{width:100%;padding:14px 16px;border:1px solid #0f3460;border-radius:8px;background:#0f3460;color:#eee;font-size:16px;transition:border-color 0.2s}.form-group input:focus{outline:none;border-color:#FF9800}.login-btn{width:100%;padding:14px;background:linear-gradient(135deg,#FF9800,#F57C00);border:none;border-radius:8px;color:white;font-size:16px;font-weight:600;cursor:pointer;transition:transform 0.2s,box-shadow 0.2s}.login-btn:hover{transform:translateY(-2px);box-shadow:0 8px 25px rgba(255,152,0,0.3)}.error-msg{background:rgba(244,67,54,0.2);color:#f44336;padding:12px;border-radius:8px;margin-bottom:20px;font-size:14px;text-align:center;display:none}.error-msg.show{display:block}</style></head><body><div class="login-container"><div class="login-header"><div class="login-icon">📡</div><h1>Peplink Manager</h1><p>Sign in to access your devices</p></div><div class="error-msg" id="errorMsg">Invalid username or password</div><form method="POST" action="/login"><div class="form-group"><label>Username</label><input type="text" name="username" required autofocus></div><div class="form-group"><label>Password</label><input type="password" name="password" required></div><button type="submit" class="login-btn">Sign In</button></form></div><script>if(window.location.search.includes('error=1')){document.getElementById('errorMsg').classList.add('show');}</script></body></html>'''

def get_main_page():
    html_path = Path(__file__).parent / 'index.html'
    return html_path.read_text()

class RequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/login':
            self.send_html(LOGIN_PAGE)
            return
        if path == '/logout':
            destroy_session(self.headers.get('Cookie'))
            self.redirect('/login', clear_session=True)
            return
        if path == '/health':
            self.send_json({'status': 'ok'})
            return
        if not verify_session(self.headers.get('Cookie'), self.headers):
            self.redirect('/login')
            return
        if path == '/':
            self.send_html(get_main_page())
        elif path == '/api/orgs':
            self.send_json(api.get('/rest/o') or [])
        elif path.startswith('/api/groups/'):
            org_id = path.split('/')[-1]
            groups = api.get(f'/rest/o/{org_id}/g') or []
            # Add lock status to groups
            for group in groups:
                group_key = f"{org_id}-{group.get('id')}"
                group['locked'] = locked_groups.get(group_key, False)
            self.send_json(groups)
        elif path.startswith('/api/devices/'):
            org_id = path.split('/')[-1]
            self.send_json(api.get(f'/rest/o/{org_id}/d') or [])
        elif path == '/api/users':
            # Get list of users (without passwords)
            users_db = load_users_from_db()
            user_list = []
            for username, info in users_db.items():
                user_list.append({'username': username, 'role': info.get('role', 'user')})
            self.send_json(user_list)
        elif path == '/api/locked-groups':
            # Get list of locked groups
            self.send_json(locked_groups)
        else:
            self.send_error(404)
    
    def do_POST(self):
        path = urlparse(self.path).path
        if path == '/login':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            params = parse_qs(post_data)
            username = params.get('username', [''])[0]
            password = params.get('password', [''])[0]
            if verify_user_password(username, password):
                session_id = create_session(username)
                self.send_response(302)
                self.send_header('Location', '/')
                self.send_header('Set-Cookie', f'session_id={session_id}; Path=/; HttpOnly; SameSite=Strict')
                self.end_headers()
                print(f'[AUTH] User \'{username}\' logged in')
            else:
                self.redirect('/login?error=1')
                print(f'[AUTH] Failed login attempt for \'{username}\'')
            return

        # All other POST endpoints require authentication
        if not verify_session(self.headers.get('Cookie'), self.headers):
            self.send_json({'error': 'Unauthorized'}, status=401)
            return

        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'

        try:
            data = json.loads(post_data) if post_data else {}
        except:
            data = {}

        if path == '/api/users':
            # Add new user
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()
            role = data.get('role', 'user')

            if not username or not password:
                self.send_json({'error': 'Username and password required'}, status=400)
                return

            users_db = load_users_from_db()
            if username in users_db:
                self.send_json({'error': 'User already exists'}, status=400)
                return

            users_db[username] = {
                'password': encrypt_password(password),
                'role': role
            }
            save_users_to_db(users_db)
            print(f'[USERS] Added new user: {username}')
            self.send_json({'success': True, 'username': username})

        elif path == '/api/group-lock':
            # Toggle group lock status
            global locked_groups
            org_id = data.get('org_id')
            group_id = data.get('group_id')
            locked = data.get('locked', False)

            if not org_id or not group_id:
                self.send_json({'error': 'org_id and group_id required'}, status=400)
                return

            group_key = f"{org_id}-{group_id}"
            if locked:
                locked_groups[group_key] = True
                print(f'[GROUPS] Locked group: {group_key}')
            else:
                locked_groups.pop(group_key, None)
                print(f'[GROUPS] Unlocked group: {group_key}')

            save_locked_groups(locked_groups)
            self.send_json({'success': True, 'locked': locked})

        elif path.startswith('/api/ic2/'):
            # Proxy POST requests to IC2 API
            ic2_path = path.replace('/api/ic2', '/rest')
            result = api.post(ic2_path, data)
            if result:
                self.send_json(result)
            else:
                self.send_json({'error': 'IC2 API request failed'}, status=500)

        else:
            self.send_error(404)

    def do_PUT(self):
        """Handle PUT requests"""
        if not verify_session(self.headers.get('Cookie'), self.headers):
            self.send_json({'error': 'Unauthorized'}, status=401)
            return

        path = urlparse(self.path).path
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'

        try:
            data = json.loads(post_data) if post_data else {}
        except:
            data = {}

        if path.startswith('/api/users/'):
            # Update user password
            username = path.split('/')[-1]
            password = data.get('password', '').strip()

            if not password:
                self.send_json({'error': 'Password required'}, status=400)
                return

            users_db = load_users_from_db()
            if username not in users_db:
                self.send_json({'error': 'User not found'}, status=404)
                return

            users_db[username]['password'] = encrypt_password(password)
            save_users_to_db(users_db)
            print(f'[USERS] Updated password for user: {username}')
            self.send_json({'success': True})

        elif path.startswith('/api/ic2/'):
            # Proxy PUT requests to IC2 API
            ic2_path = path.replace('/api/ic2', '/rest')
            result = api.put(ic2_path, data)
            if result:
                self.send_json(result)
            else:
                self.send_json({'error': 'IC2 API request failed'}, status=500)

        else:
            self.send_error(404)

    def do_DELETE(self):
        """Handle DELETE requests"""
        if not verify_session(self.headers.get('Cookie'), self.headers):
            self.send_json({'error': 'Unauthorized'}, status=401)
            return

        path = urlparse(self.path).path

        if path.startswith('/api/users/'):
            # Delete user
            username = path.split('/')[-1]

            users_db = load_users_from_db()
            if username not in users_db:
                self.send_json({'error': 'User not found'}, status=404)
                return

            if username == 'alex':
                self.send_json({'error': 'Cannot delete default admin user'}, status=403)
                return

            del users_db[username]
            save_users_to_db(users_db)
            print(f'[USERS] Deleted user: {username}')
            self.send_json({'success': True})

        elif path.startswith('/api/ic2/'):
            # Proxy DELETE requests to IC2 API
            ic2_path = path.replace('/api/ic2', '/rest')
            result = api.delete(ic2_path)
            if result:
                self.send_json(result)
            else:
                self.send_json({'error': 'IC2 API request failed'}, status=500)

        else:
            self.send_error(404)

    def send_html(self, content):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(content.encode())
    
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def redirect(self, location, clear_session=False):
        self.send_response(302)
        self.send_header('Location', location)
        if clear_session:
            self.send_header('Set-Cookie', 'session_id=; Path=/; Max-Age=0')
        self.end_headers()
    
    def log_message(self, format, *args):
        print(f'[HTTP] {self.address_string()} - {format % args}')

class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

def run_server(port=8000):
    print('=' * 50)
    print('  Peplink InControl2 Manager')
    print('=' * 50)
    print(f'  Port: {port}')
    print(f'  API:  {CONFIG["api_url"]}')
    print('=' * 50)
    api.authenticate()
    with ReusableTCPServer(('0.0.0.0', port), RequestHandler) as httpd:
        print(f'\n[SERVER] Running at http://localhost:{port}')
        print('[SERVER] Press Ctrl+C to stop\n')
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\n[SERVER] Shutting down...')

if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else CONFIG['port']
    run_server(port)
