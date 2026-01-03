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
from urllib.parse import urlparse, parse_qs
from http.cookies import SimpleCookie
from pathlib import Path

CONFIG = {
    'client_id': os.environ.get('PEPLINK_CLIENT_ID', '1c7314d2ecc9c04138e5c7f0d1b538c9'),
    'client_secret': os.environ.get('PEPLINK_CLIENT_SECRET', '75fb1e2a82fa9ef06380a760d8b96b0e'),
    'api_url': os.environ.get('PEPLINK_API_URL', 'https://api.ic.peplink.com'),
    'port': int(os.environ.get('PORT', 8000)),
}

DEFAULT_USERS = {'alex': 'hyrox'}

def load_users():
    users_env = os.environ.get('PEPLINK_USERS', '')
    if users_env:
        users = {}
        for pair in users_env.split(','):
            if ':' in pair:
                user, passwd = pair.split(':', 1)
                users[user.strip()] = hashlib.sha256(passwd.strip().encode()).hexdigest()
        return users
    return {u: hashlib.sha256(p.encode()).hexdigest() for u, p in DEFAULT_USERS.items()}

USERS = load_users()

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

api = PeplinkAPI(CONFIG['client_id'], CONFIG['client_secret'], CONFIG['api_url'])
sessions = {}

def create_session(username):
    session_id = secrets.token_hex(32)
    sessions[session_id] = {'username': username}
    return session_id

def verify_session(cookie_header):
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
        if not verify_session(self.headers.get('Cookie')):
            self.redirect('/login')
            return
        if path == '/':
            self.send_html(get_main_page())
        elif path == '/api/orgs':
            self.send_json(api.get('/rest/o') or [])
        elif path.startswith('/api/groups/'):
            org_id = path.split('/')[-1]
            self.send_json(api.get(f'/rest/o/{org_id}/g') or [])
        elif path.startswith('/api/devices/'):
            org_id = path.split('/')[-1]
            self.send_json(api.get(f'/rest/o/{org_id}/d') or [])
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
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if username in USERS and USERS[username] == password_hash:
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
        self.send_error(404)
    
    def send_html(self, content):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(content.encode())
    
    def send_json(self, data):
        self.send_response(200)
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
