# ============================================
# MEZANEYO SCHOOL - Flask Backend
# Using Supabase
# ============================================

from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import json
from datetime import datetime
import uuid

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'c0b06cdcf564ac883d6a78948d560393cad025186db688573885f13c2a9f5565')
CORS(app, supports_credentials=True)

# ============================================
# SUPABASE CONFIGURATION
# ============================================

SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://nivmrwbusbeppdssmfpj.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_ANON_KEY', 'sb_publishable_kwF_yAmJ5AWnbaIe57snrw_fXng7-6a')

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Supabase connected successfully!")
except Exception as e:
    print(f"❌ Supabase connection error: {e}")
    supabase = None

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
    if not supabase:
        return jsonify({"success": False, "error": "Supabase not connected"}), 500
    
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        full_name = data.get('full_name')
        role = data.get('role', 'student')
        
        if not email or not password or not full_name:
            return jsonify({"success": False, "error": "All fields are required"}), 400
        
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
            # Save to users table
            try:
                supabase.table('users').insert({
                    "auth_user_id": response.user.id,
                    "email": email,
                    "full_name": full_name,
                    "role": role
                }).execute()
            except Exception as e:
                print(f"User table insert error: {e}")
            
            return jsonify({
                "success": True,
                "message": "User registered successfully",
                "user": {
                    "id": response.user.id,
                    "email": email,
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
    if not supabase:
        return jsonify({"success": False, "error": "Supabase not connected"}), 500
    
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({"success": False, "error": "Email and password required"}), 400
        
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
    session.clear()
    return jsonify({"success": True, "message": "Logged out"})

@app.route('/api/auth/me', methods=['GET'])
def get_current_user():
    if 'user' in session:
        return jsonify({"success": True, "user": session['user']})
    return jsonify({"success": False, "error": "Not logged in"}), 401

# ============================================
# API - STUDENTS
# ============================================

@app.route('/api/students', methods=['GET'])
def get_students():
    if not supabase:
        return jsonify({"success": False, "error": "Supabase not connected"}), 500
    
    try:
        response = supabase.table('students').select('*').execute()
        return jsonify({"success": True, "students": response.data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/students', methods=['POST'])
def create_student():
    if not supabase:
        return jsonify({"success": False, "error": "Supabase not connected"}), 500
    
    try:
        data = request.get_json()
        response = supabase.table('students').insert(data).execute()
        return jsonify({"success": True, "student": response.data[0] if response.data else {}})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/students/<student_id>', methods=['DELETE'])
def delete_student(student_id):
    if not supabase:
        return jsonify({"success": False, "error": "Supabase not connected"}), 500
    
    try:
        supabase.table('students').delete().eq('id', student_id).execute()
        return jsonify({"success": True, "message": "Student deleted"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================
# API - TEACHERS
# ============================================

@app.route('/api/teachers', methods=['GET'])
def get_teachers():
    if not supabase:
        return jsonify({"success": False, "error": "Supabase not connected"}), 500
    
    try:
        response = supabase.table('teachers').select('*').execute()
        return jsonify({"success": True, "teachers": response.data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/teachers', methods=['POST'])
def create_teacher():
    if not supabase:
        return jsonify({"success": False, "error": "Supabase not connected"}), 500
    
    try:
        data = request.get_json()
        response = supabase.table('teachers').insert(data).execute()
        return jsonify({"success": True, "teacher": response.data[0] if response.data else {}})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/teachers/<teacher_id>', methods=['DELETE'])
def delete_teacher(teacher_id):
    if not supabase:
        return jsonify({"success": False, "error": "Supabase not connected"}), 500
    
    try:
        supabase.table('teachers').delete().eq('id', teacher_id).execute()
        return jsonify({"success": True, "message": "Teacher deleted"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================
# API - CLASSES
# ============================================

@app.route('/api/classes', methods=['GET'])
def get_classes():
    if not supabase:
        return jsonify({"success": False, "error": "Supabase not connected"}), 500
    
    try:
        response = supabase.table('classes').select('*, forms(name), teachers(full_name)').execute()
        return jsonify({"success": True, "classes": response.data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/classes', methods=['POST'])
def create_class():
    if not supabase:
        return jsonify({"success": False, "error": "Supabase not connected"}), 500
    
    try:
        data = request.get_json()
        response = supabase.table('classes').insert(data).execute()
        return jsonify({"success": True, "class": response.data[0] if response.data else {}})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================
# API - SUBJECTS
# ============================================

@app.route('/api/subjects', methods=['GET'])
def get_subjects():
    if not supabase:
        return jsonify({"success": False, "error": "Supabase not connected"}), 500
    
    try:
        response = supabase.table('subjects').select('*').execute()
        return jsonify({"success": True, "subjects": response.data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/subjects', methods=['POST'])
def create_subject():
    if not supabase:
        return jsonify({"success": False, "error": "Supabase not connected"}), 500
    
    try:
        data = request.get_json()
        response = supabase.table('subjects').insert(data).execute()
        return jsonify({"success": True, "subject": response.data[0] if response.data else {}})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================
# API - FORMS
# ============================================

@app.route('/api/forms', methods=['GET'])
def get_forms():
    if not supabase:
        return jsonify({"success": False, "error": "Supabase not connected"}), 500
    
    try:
        response = supabase.table('forms').select('*').order('name').execute()
        return jsonify({"success": True, "forms": response.data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/form-subjects/<form_id>', methods=['GET'])
def get_form_subjects(form_id):
    if not supabase:
        return jsonify({"success": False, "error": "Supabase not connected"}), 500
    
    try:
        response = supabase.table('form_subjects') \
            .select('subject_id, is_compulsory, is_optional, is_root, subjects(id, name, category)') \
            .eq('form_id', form_id) \
            .execute()
        return jsonify({"success": True, "subjects": response.data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================
# API - ANNOUNCEMENTS
# ============================================

@app.route('/api/announcements', methods=['GET'])
def get_announcements():
    if not supabase:
        return jsonify({"success": False, "error": "Supabase not connected"}), 500
    
    try:
        response = supabase.table('announcements').select('*').order('created_at', desc=True).execute()
        return jsonify({"success": True, "announcements": response.data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/announcements', methods=['POST'])
def create_announcement():
    if not supabase:
        return jsonify({"success": False, "error": "Supabase not connected"}), 500
    
    try:
        data = request.get_json()
        response = supabase.table('announcements').insert(data).execute()
        return jsonify({"success": True, "announcement": response.data[0] if response.data else {}})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/announcements/<announcement_id>', methods=['DELETE'])
def delete_announcement(announcement_id):
    if not supabase:
        return jsonify({"success": False, "error": "Supabase not connected"}), 500
    
    try:
        supabase.table('announcements').delete().eq('id', announcement_id).execute()
        return jsonify({"success": True, "message": "Announcement deleted"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================
# API - USERS
# ============================================

@app.route('/api/users', methods=['GET'])
def get_users():
    if not supabase:
        return jsonify({"success": False, "error": "Supabase not connected"}), 500
    
    try:
        response = supabase.table('users').select('*').order('created_at', desc=True).execute()
        return jsonify({"success": True, "users": response.data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    if not supabase:
        return jsonify({"success": False, "error": "Supabase not connected"}), 500
    
    try:
        supabase.table('users').delete().eq('id', user_id).execute()
        return jsonify({"success": True, "message": "User deleted"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================
# API - HEALTH CHECK
# ============================================

@app.route('/api/health')
def health_check():
    status = "healthy" if supabase else "unhealthy"
    return jsonify({
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "supabase": "connected" if supabase else "disconnected"
    })

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
