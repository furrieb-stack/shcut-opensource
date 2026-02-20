# backend/app.py

from flask import Flask, render_template, request, jsonify, session, redirect, abort
from flask_cors import CORS
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import re
import requests
import json
import threading
from datetime import datetime
import os
from dotenv import load_dotenv
from user_agents import parse
from urllib.parse import urlparse

load_dotenv()

app = Flask(__name__,
            template_folder='../frontend/templates',
            static_folder='../frontend/static')

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False
CORS(app, supports_credentials=True, origins=["http://localhost:5000", "http://127.0.0.1:5000"])

WEBHOOK_URL = "https://discord.com/api/webhooks/1474500737844379658/peUQqcBQVUqzoIo4do9I7EOJxNOapZJH3FHUZDo5LYePnpShmm1g5YpThd51mcICQc3a" #change on your own

def sanitize_webhook_input(text, max_length=100):
    if not text:
        return ""
    text = re.sub(r'[@#]', '', text)
    markdown_chars = ['*', '_', '`', '~', '>', '|']
    for char in markdown_chars:
        text = text.replace(char, f'\\{char}')
    text = re.sub(r'[\n\r\t]', ' ', text)
    return text[:max_length]

def validate_url_for_webhook(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ['http', 'https']:
            return False
        if len(url) > 500:
            return False
        if any(c in url for c in ['\n', '\r', '\t', '@', '#']):
            return False
        return True
    except:
        return False

def send_discord_webhook_async(event_type, data):
    def _send():
        try:
            payload = {
                "allowed_mentions": {"parse": []},
                "embeds": [{
                    "color": 3447003,
                    "fields": []
                }]
            }
            
            if event_type == 'url_created':
                safe_original = sanitize_webhook_input(data['original_url'], 50)
                if not validate_url_for_webhook(data['original_url']):
                    safe_original = "[Invalid URL]"
                
                payload["embeds"][0]["title"] = "🔗 New URL Created"
                payload["embeds"][0]["fields"] = [
                    {"name": "User", "value": sanitize_webhook_input(data['username'], 20), "inline": True},
                    {"name": "Short Code", "value": sanitize_webhook_input(data['short_code'], 10), "inline": True},
                    {"name": "Original URL", "value": safe_original, "inline": False},
                    {"name": "Short URL", "value": sanitize_webhook_input(data['short_url'], 50), "inline": False},
                    {"name": "Timestamp", "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "inline": True}
                ]
            elif event_type == 'user_registered':
                payload["embeds"][0]["title"] = "👤 New User Registered"
                payload["embeds"][0]["color"] = 3066993
                payload["embeds"][0]["fields"] = [
                    {"name": "Username", "value": sanitize_webhook_input(data['username'], 20), "inline": True},
                    {"name": "Email", "value": sanitize_webhook_input(data['email'], 30), "inline": True},
                    {"name": "User ID", "value": str(data['user_id']), "inline": True},
                    {"name": "Timestamp", "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "inline": True}
                ]
            elif event_type == 'url_deleted':
                safe_original = sanitize_webhook_input(data['original_url'], 50)
                payload["embeds"][0]["title"] = "🗑️ URL Deleted"
                payload["embeds"][0]["color"] = 15158332
                payload["embeds"][0]["fields"] = [
                    {"name": "User", "value": sanitize_webhook_input(data['username'], 20), "inline": True},
                    {"name": "Short Code", "value": sanitize_webhook_input(data['short_code'], 10), "inline": True},
                    {"name": "Original URL", "value": safe_original, "inline": False},
                    {"name": "Timestamp", "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "inline": True}
                ]
            
            requests.post(WEBHOOK_URL, json=payload, timeout=2)
        except:
            pass
    
    thread = threading.Thread(target=_send)
    thread.daemon = True
    thread.start()

def get_client_info(request):
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ',' in ip:
        ip = ip.split(',')[0].strip()
    
    try:
        response = requests.get(f'http://ip-api.com/json/{ip}', timeout=2)
        if response.status_code == 200:
            data = response.json()
            return {
                'ip': ip[:45],
                'country': data.get('countryCode', 'UN')[:2],
                'city': (data.get('city', 'Unknown') or 'Unknown')[:100],
                'region': (data.get('regionName', 'Unknown') or 'Unknown')[:100],
                'isp': (data.get('isp', 'Unknown') or 'Unknown')[:200],
                'lat': data.get('lat', 0),
                'lon': data.get('lon', 0)
            }
    except:
        pass
    
    return {
        'ip': ip[:45],
        'country': 'UN',
        'city': 'Unknown',
        'region': 'Unknown',
        'isp': 'Unknown',
        'lat': 0,
        'lon': 0
    }

def get_db():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        port=int(os.getenv('DB_PORT', 20269)),
        database=os.getenv('DB_NAME', 'shcut')
    )

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stats/<short_code>')
def stats_page(short_code):
    if 'user_id' not in session:
        return redirect('/')
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        'SELECT id FROM urls WHERE short_code = %s AND user_id = %s',
        (short_code, session['user_id'])
    )
    url = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not url:
        abort(404)
    
    return render_template('stats.html', short_code=short_code)

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not all([username, email, password]):
        return jsonify({'error': 'All fields required'}), 400
    
    if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
        return jsonify({'error': 'Invalid username format'}), 400
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute('SELECT id FROM users WHERE username = %s OR email = %s', (username, email))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({'error': 'User already exists'}), 409
    
    password_hash = generate_password_hash(password)
    api_key = secrets.token_urlsafe(32)
    
    cursor.execute(
        'INSERT INTO users (username, email, password_hash, api_key, created_at) VALUES (%s, %s, %s, %s, %s)',
        (username, email, password_hash, api_key, datetime.now())
    )
    conn.commit()
    user_id = cursor.lastrowid
    cursor.close()
    conn.close()
    
    session['user_id'] = user_id
    session['username'] = username
    
    send_discord_webhook_async('user_registered', {
        'username': username,
        'email': email,
        'user_id': user_id
    })
    
    return jsonify({'message': 'Registration successful'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not all([username, password]):
        return jsonify({'error': 'Username and password required'}), 400
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute('SELECT id, username, password_hash FROM users WHERE username = %s', (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    session['user_id'] = user['id']
    session['username'] = user['username']
    
    return jsonify({'message': 'Login successful'}), 200

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logout successful'}), 200

@app.route('/api/urls', methods=['GET'])
def get_urls():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute(
        'SELECT short_code, original_url, clicks, created_at FROM urls WHERE user_id = %s ORDER BY created_at DESC LIMIT 5',
        (session['user_id'],)
    )
    urls = cursor.fetchall()
    cursor.close()
    conn.close()
    
    for url in urls:
        url['short_url'] = f"{request.host_url}{url['short_code']}"
        url['stats_url'] = f"{request.host_url}stats/{url['short_code']}"
        url['created_at'] = url['created_at'].isoformat()
    
    return jsonify(urls), 200

@app.route('/api/url/<short_code>/clicks', methods=['GET'])
def get_url_clicks(short_code):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute(
        'SELECT clicks FROM urls WHERE short_code = %s AND user_id = %s',
        (short_code, session['user_id'])
    )
    url = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not url:
        return jsonify({'error': 'URL not found'}), 404
    
    return jsonify({'clicks': url['clicks']}), 200

@app.route('/api/url/<short_code>/stats', methods=['GET'])
def get_url_stats(short_code):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute(
        'SELECT id, short_code, original_url, clicks, created_at FROM urls WHERE short_code = %s AND user_id = %s',
        (short_code, session['user_id'])
    )
    url = cursor.fetchone()
    
    if not url:
        cursor.close()
        conn.close()
        return jsonify({'error': 'URL not found'}), 404
    
    url_id = url['id']
    
    cursor.execute(
        '''SELECT 
            COUNT(*) as total_clicks,
            COUNT(DISTINCT ip_address) as unique_visitors,
            COUNT(DISTINCT country) as unique_countries
           FROM analytics WHERE url_id = %s''',
        (url_id,)
    )
    stats = cursor.fetchone()
    
    cursor.execute(
        'SELECT COUNT(*) as today_clicks FROM analytics WHERE url_id = %s AND DATE(clicked_at) = CURDATE()',
        (url_id,)
    )
    today = cursor.fetchone()
    
    cursor.execute(
        'SELECT COUNT(*) as week_clicks FROM analytics WHERE url_id = %s AND clicked_at >= NOW() - INTERVAL 7 DAY',
        (url_id,)
    )
    week = cursor.fetchone()
    
    cursor.execute(
        '''SELECT 
            COALESCE(country, 'UN') as country,
            COUNT(*) as count
           FROM analytics 
           WHERE url_id = %s
           GROUP BY country
           ORDER BY count DESC''',
        (url_id,)
    )
    countries = cursor.fetchall()
    
    total = stats['total_clicks'] or 1
    for c in countries:
        c['percentage'] = (c['count'] / total) * 100
    
    cursor.execute(
        '''SELECT 
            DATE(clicked_at) as date,
            COUNT(*) as clicks
           FROM analytics 
           WHERE url_id = %s AND clicked_at >= NOW() - INTERVAL 30 DAY
           GROUP BY DATE(clicked_at)
           ORDER BY date DESC''',
        (url_id,)
    )
    timeline = cursor.fetchall()
    
    cursor.execute(
        '''SELECT 
            ip_address,
            country,
            city,
            device_type,
            browser,
            os,
            clicked_at
           FROM analytics 
           WHERE url_id = %s
           ORDER BY clicked_at DESC
           LIMIT 50''',
        (url_id,)
    )
    recent_clicks = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return jsonify({
        'url': {
            'short_code': url['short_code'],
            'original_url': url['original_url'],
            'short_url': f"{request.host_url}{url['short_code']}",
            'created_at': url['created_at'].isoformat(),
            'total_clicks': url['clicks']
        },
        'stats': {
            'total_clicks': stats['total_clicks'] or 0,
            'unique_visitors': stats['unique_visitors'] or 0,
            'unique_countries': stats['unique_countries'] or 0,
            'today_clicks': today['today_clicks'] or 0,
            'week_clicks': week['week_clicks'] or 0
        },
        'countries': countries,
        'timeline': timeline,
        'recent_clicks': recent_clicks
    }), 200

@app.route('/api/url/<short_code>/settings', methods=['GET'])
def get_url_settings(short_code):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute(
        'SELECT blocked_countries, max_clicks, expires_at FROM urls WHERE short_code = %s AND user_id = %s',
        (short_code, session['user_id'])
    )
    url = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not url:
        return jsonify({'error': 'URL not found'}), 404
    
    return jsonify({
        'blocked_countries': json.loads(url['blocked_countries']) if url['blocked_countries'] else [],
        'max_clicks': url['max_clicks'],
        'expires_at': url['expires_at'].isoformat() if url['expires_at'] else None
    }), 200

@app.route('/api/url/<short_code>/settings', methods=['PUT'])
def update_url_settings(short_code):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    blocked_countries = data.get('blocked_countries', [])
    max_clicks = data.get('max_clicks')
    expires_at = data.get('expires_at')
    
    if not isinstance(blocked_countries, list):
        return jsonify({'error': 'blocked_countries must be a list'}), 400
    
    if max_clicks and (not isinstance(max_clicks, int) or max_clicks < 1):
        return jsonify({'error': 'max_clicks must be a positive integer'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        '''UPDATE urls SET 
           blocked_countries = %s,
           max_clicks = %s,
           expires_at = %s
           WHERE short_code = %s AND user_id = %s''',
        (json.dumps(blocked_countries), max_clicks, expires_at, short_code, session['user_id'])
    )
    conn.commit()
    affected = cursor.rowcount
    cursor.close()
    conn.close()
    
    if affected:
        return jsonify({'message': 'Settings updated'}), 200
    return jsonify({'error': 'URL not found'}), 404

@app.route('/api/shorten', methods=['POST'])
def shorten_url():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    original_url = data.get('url')
    
    if not original_url:
        return jsonify({'error': 'URL required'}), 400
    
    if not original_url.startswith(('http://', 'https://')):
        original_url = 'https://' + original_url
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute(
        'SELECT COUNT(*) as count FROM urls WHERE user_id = %s',
        (session['user_id'],)
    )
    count = cursor.fetchone()['count']
    
    if count >= 5:
        cursor.close()
        conn.close()
        return jsonify({'error': 'Maximum 5 URLs allowed'}), 403
    
    short_code = secrets.token_urlsafe(6)
    
    cursor.execute(
        'INSERT INTO urls (user_id, original_url, short_code, clicks, created_at, blocked_countries) VALUES (%s, %s, %s, 0, %s, %s)',
        (session['user_id'], original_url, short_code, datetime.now(), '[]')
    )
    conn.commit()
    cursor.close()
    conn.close()
    
    short_url = f"{request.host_url}{short_code}"
    stats_url = f"{request.host_url}stats/{short_code}"
    
    send_discord_webhook_async('url_created', {
        'username': session['username'],
        'short_code': short_code,
        'original_url': original_url,
        'short_url': short_url
    })
    
    return jsonify({
        'short_code': short_code,
        'short_url': short_url,
        'stats_url': stats_url,
        'original_url': original_url,
        'clicks': 0,
        'created_at': datetime.now().isoformat()
    }), 201

@app.route('/api/url/<short_code>', methods=['DELETE'])
def delete_url(short_code):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute(
        'SELECT original_url FROM urls WHERE short_code = %s AND user_id = %s',
        (short_code, session['user_id'])
    )
    url = cursor.fetchone()
    
    if not url:
        cursor.close()
        conn.close()
        return jsonify({'error': 'URL not found'}), 404
    
    cursor.execute(
        'DELETE FROM urls WHERE short_code = %s AND user_id = %s',
        (short_code, session['user_id'])
    )
    conn.commit()
    cursor.close()
    conn.close()
    
    send_discord_webhook_async('url_deleted', {
        'username': session['username'],
        'short_code': short_code,
        'original_url': url['original_url']
    })
    
    return jsonify({'message': 'URL deleted'}), 200

@app.route('/<short_code>')
def redirect_to_url(short_code):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute(
        '''SELECT id, original_url, clicks, blocked_countries, max_clicks, expires_at 
           FROM urls WHERE short_code = %s''',
        (short_code,)
    )
    url = cursor.fetchone()
    
    if not url:
        cursor.close()
        conn.close()
        abort(404)
    
    if url['expires_at'] and url['expires_at'] < datetime.now():
        cursor.close()
        conn.close()
        return 'Link expired', 410
    
    if url['max_clicks'] and url['clicks'] >= url['max_clicks']:
        cursor.close()
        conn.close()
        return 'Maximum clicks reached', 410
    
    client_info = get_client_info(request)
    
    if url['blocked_countries']:
        blocked = json.loads(url['blocked_countries'])
        if client_info['country'] in blocked:
            cursor.close()
            conn.close()
            return 'Access denied from your country', 403
    
    ua_string = request.headers.get('User-Agent', '')
    ua = parse(ua_string)
    
    try:
        cursor.execute(
            '''INSERT INTO analytics 
               (url_id, ip_address, country, city, region, isp, lat, lon, 
                device_type, browser, os, user_agent, referer) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
            (
                url['id'], 
                client_info['ip'], 
                client_info['country'],
                client_info['city'], 
                client_info['region'], 
                client_info['isp'],
                client_info['lat'], 
                client_info['lon'],
                (ua.device.family or 'Unknown')[:50],
                (ua.browser.family or 'Unknown')[:50],
                (ua.os.family or 'Unknown')[:50],
                ua_string[:500], 
                (request.headers.get('Referer', '') or '')[:500]
            )
        )
    except Exception as e:
        print(f"Analytics error: {e}")
    
    cursor.execute('UPDATE urls SET clicks = clicks + 1 WHERE id = %s', (url['id'],))
    conn.commit()
    cursor.close()
    conn.close()
    
    return redirect(url['original_url'])

if __name__ == '__main__':
    app.run(debug=True, port=5000)