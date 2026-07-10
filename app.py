# ============================================
# MEZANEYO SCHOOL - Flask Backend
# ============================================

import os
import json
import uuid
import datetime
import base64
from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
from flask_cors import CORS
from supabase import create_client, Client
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================
# CONFIGURATION
# ============================================

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'c0b06cdcf564ac883d6a78948d560393cad025186db688573885f13c2a9f5565')
CORS(app, supports_credentials=True)

# Supabase Configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://nivmrwbusbeppdssmfpj.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_ANON_KEY', 'sb_publishable_kwF_yAmJ5AWnbaIe57snrw_fXng7-6a')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Upload Configuration
UPLOAD_FOLDER = 'uploads/recordings'
ALLOWED_EXTENSIONS = {'mp4', 'webm', 'mov', 'avi', 'mkv', 'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'ppt', 'pptx'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ============================================
# ROUTES - MAIN PAGES
# ============================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/signup')
def signup_page():
    return render_template('signup.html')

@app.route('/admin-dashboard')
def admin_dashboard():
    return render_template('admin-dashboard.html')

@app.route('/teacher-dashboard')
def teacher_dashboard():
    return render_template('teacher-dashboard.html')

@app.route('/student-dashboard')
def student_dashboard():
    return render_template('student-dashboard.html')

@app.route('/whiteboard')
def whiteboard():
    return render_template('whiteboard.html')

@app.route('/forum')
def forum():
    return render_template('forum.html')

@app.route('/forgot-password')
def forgot_password():
    return render_template('forgot-password.html')

@app.route('/reset-password')
def reset_password():
    return render_template('reset-password.html')

@app.route('/confirm-email')
def confirm_email():
    return render_template('confirm-email.html')

# ============================================
# API - AUTHENTICATION
# ============================================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        full_name = data.get('full_name')
        role = data.get('role', 'student')
        
        # Register with Supabase Auth
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "full_name": full_name,
                    "role": role
                }
            }
        })
        
        if response.user:
            # Create user record in users table
            supabase.table('users').insert({
                "email": email,
                "full_name": full_name,
                "role": role,
                "auth_user_id": response.user.id
            }).execute()
            
            return jsonify({
                "success": True,
                "message": "User registered successfully",
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "full_name": full_name,
                    "role": role
                }
            })
        else:
            return jsonify({"success": False, "error": "Registration failed"}), 400
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.user:
            session['user'] = {
                "id": response.user.id,
                "email": response.user.email,
                "full_name": response.user.user_metadata.get('full_name', email),
                "role": response.user.user_metadata.get('role', 'student')
            }
            
            return jsonify({
                "success": True,
                "message": "Login successful",
                "user": session['user']
            })
        else:
            return jsonify({"success": False, "error": "Invalid credentials"}), 401
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logout user"""
    session.clear()
    return jsonify({"success": True, "message": "Logged out"})

@app.route('/api/auth/me', methods=['GET'])
def get_current_user():
    """Get current user"""
    if 'user' in session:
        return jsonify({"success": True, "user": session['user']})
    return jsonify({"success": False, "error": "Not logged in"}), 401

# ============================================
# API - HEALTH CHECK
# ============================================

@app.route('/api/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat()
    })

# ============================================
# STATIC FILES
# ============================================

@app.route('/uploads/recordings/<filename>')
def serve_recording(filename):
    """Serve recorded video files"""
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        return send_file(filepath, mimetype='video/mp4')
    return jsonify({"error": "File not found"}), 404

# ============================================
# ERROR HANDLING
# ============================================

@app.errorhandler(404)
def not_found(e):
    return render_template('index.html'), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"success": False, "error": "Internal server error"}), 500

# ============================================
# RUN
# ============================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
