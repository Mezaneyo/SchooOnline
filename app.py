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
import requests

# ============================================
# CONFIGURATION
# ============================================

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app)

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
# API - STUDENTS
# ============================================

@app.route('/api/students', methods=['GET'])
def get_students():
    """Get all students"""
    try:
        response = supabase.table('students').select('*, classes(class_name)').order('created_at', desc=True).execute()
        return jsonify({"success": True, "students": response.data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/students', methods=['POST'])
def create_student():
    """Create a new student"""
    try:
        data = request.get_json()
        response = supabase.table('students').insert({
            "full_name": data.get('full_name'),
            "student_id_number": data.get('student_id_number'),
            "class_id": data.get('class_id'),
            "guardian_name": data.get('guardian_name'),
            "guardian_phone": data.get('guardian_phone'),
            "guardian_email": data.get('guardian_email')
        }).execute()
        return jsonify({"success": True, "student": response.data[0] if response.data else {}})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/students/<student_id>', methods=['PUT'])
def update_student(student_id):
    """Update a student"""
    try:
        data = request.get_json()
        response = supabase.table('students').update(data).eq('id', student_id).execute()
        return jsonify({"success": True, "student": response.data[0] if response.data else {}})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/students/<student_id>', methods=['DELETE'])
def delete_student(student_id):
    """Delete a student"""
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
    """Get all teachers"""
    try:
        response = supabase.table('teachers').select('*, teacher_classes(class_id), classes(class_name)').order('created_at', desc=True).execute()
        return jsonify({"success": True, "teachers": response.data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/teachers', methods=['POST'])
def create_teacher():
    """Create a new teacher"""
    try:
        data = request.get_json()
        response = supabase.table('teachers').insert({
            "full_name": data.get('full_name'),
            "email": data.get('email'),
            "subject_specialty": data.get('subject_specialty'),
            "employee_id": data.get('employee_id'),
            "is_active": True
        }).execute()
        
        teacher = response.data[0] if response.data else {}
        
        # Assign to class if provided
        if teacher and data.get('class_id'):
            supabase.table('teacher_classes').insert({
                "teacher_id": teacher['id'],
                "class_id": data.get('class_id')
            }).execute()
        
        return jsonify({"success": True, "teacher": teacher})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/teachers/<teacher_id>', methods=['DELETE'])
def delete_teacher(teacher_id):
    """Delete a teacher"""
    try:
        # Delete from teacher_classes first
        supabase.table('teacher_classes').delete().eq('teacher_id', teacher_id).execute()
        # Delete teacher
        supabase.table('teachers').delete().eq('id', teacher_id).execute()
        return jsonify({"success": True, "message": "Teacher deleted"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================
# API - CLASSES
# ============================================

@app.route('/api/classes', methods=['GET'])
def get_classes():
    """Get all classes"""
    try:
        response = supabase.table('classes').select('*, forms(name), teachers(full_name)').order('created_at', desc=True).execute()
        return jsonify({"success": True, "classes": response.data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/classes', methods=['POST'])
def create_class():
    """Create a new class"""
    try:
        data = request.get_json()
        response = supabase.table('classes').insert({
            "class_name": data.get('class_name'),
            "form_id": data.get('form_id'),
            "class_teacher_id": data.get('class_teacher_id'),
            "academic_year": data.get('academic_year', '2026')
        }).execute()
        return jsonify({"success": True, "class": response.data[0] if response.data else {}})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================
# API - SUBJECTS
# ============================================

@app.route('/api/subjects', methods=['GET'])
def get_subjects():
    """Get all subjects"""
    try:
        response = supabase.table('subjects').select('*').order('category', asc=True).execute()
        return jsonify({"success": True, "subjects": response.data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/subjects', methods=['POST'])
def create_subject():
    """Create a new subject"""
    try:
        data = request.get_json()
        response = supabase.table('subjects').insert({
            "name": data.get('name'),
            "category": data.get('category', 'compulsory')
        }).execute()
        return jsonify({"success": True, "subject": response.data[0] if response.data else {}})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================
# API - LESSONS
# ============================================

@app.route('/api/lessons', methods=['GET'])
def get_lessons():
    """Get lessons for a class"""
    try:
        class_id = request.args.get('class_id')
        if not class_id:
            return jsonify({"success": False, "error": "class_id required"}), 400
        
        response = supabase.table('lessons') \
            .select('*, teachers(full_name), subjects(name)') \
            .eq('class_id', class_id) \
            .eq('is_published', True) \
            .order('created_at', desc=True) \
            .execute()
        
        return jsonify({"success": True, "lessons": response.data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/lessons', methods=['POST'])
def create_lesson():
    """Create a new lesson"""
    try:
        data = request.get_json()
        response = supabase.table('lessons').insert({
            "teacher_id": data.get('teacher_id'),
            "class_id": data.get('class_id'),
            "subject_id": data.get('subject_id'),
            "title": data.get('title'),
            "content": data.get('content'),
            "lesson_type": data.get('lesson_type', 'text'),
            "video_url": data.get('video_url'),
            "is_published": True
        }).execute()
        return jsonify({"success": True, "lesson": response.data[0] if response.data else {}})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================
# API - ASSIGNMENTS
# ============================================

@app.route('/api/assignments', methods=['GET'])
def get_assignments():
    """Get assignments for a class"""
    try:
        class_id = request.args.get('class_id')
        if not class_id:
            return jsonify({"success": False, "error": "class_id required"}), 400
        
        response = supabase.table('assignments') \
            .select('*, teachers(full_name), subjects(name)') \
            .eq('class_id', class_id) \
            .order('due_date', asc=True) \
            .execute()
        
        return jsonify({"success": True, "assignments": response.data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/assignments', methods=['POST'])
def create_assignment():
    """Create a new assignment"""
    try:
        data = request.get_json()
        response = supabase.table('assignments').insert({
            "teacher_id": data.get('teacher_id'),
            "class_id": data.get('class_id'),
            "subject_id": data.get('subject_id'),
            "title": data.get('title'),
            "description": data.get('description'),
            "due_date": data.get('due_date'),
            "attachment_url": data.get('attachment_url')
        }).execute()
        return jsonify({"success": True, "assignment": response.data[0] if response.data else {}})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================
# API - FORUMS
# ============================================

@app.route('/api/forums', methods=['GET'])
def get_forums():
    """Get forums for a class"""
    try:
        class_id = request.args.get('class_id')
        if not class_id:
            return jsonify({"success": False, "error": "class_id required"}), 400
        
        response = supabase.table('forums') \
            .select('*, teachers(full_name)') \
            .eq('class_id', class_id) \
            .eq('is_active', True) \
            .order('created_at', desc=True) \
            .execute()
        
        return jsonify({"success": True, "forums": response.data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/forums', methods=['POST'])
def create_forum():
    """Create a new forum"""
    try:
        data = request.get_json()
        response = supabase.table('forums').insert({
            "class_id": data.get('class_id'),
            "teacher_id": data.get('teacher_id'),
            "title": data.get('title'),
            "description": data.get('description'),
            "is_active": True
        }).execute()
        return jsonify({"success": True, "forum": response.data[0] if response.data else {}})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================
# API - FORUM POSTS
# ============================================

@app.route('/api/forum-posts', methods=['GET'])
def get_forum_posts():
    """Get posts for a forum"""
    try:
        forum_id = request.args.get('forum_id')
        if not forum_id:
            return jsonify({"success": False, "error": "forum_id required"}), 400
        
        response = supabase.table('forum_posts') \
            .select('*') \
            .eq('forum_id', forum_id) \
            .order('is_pinned', desc=True) \
            .order('created_at', desc=True) \
            .execute()
        
        return jsonify({"success": True, "posts": response.data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/forum-posts', methods=['POST'])
def create_forum_post():
    """Create a new forum post"""
    try:
        data = request.get_json()
        response = supabase.table('forum_posts').insert({
            "forum_id": data.get('forum_id'),
            "user_id": data.get('user_id'),
            "user_name": data.get('user_name'),
            "title": data.get('title'),
            "content": data.get('content'),
            "is_pinned": data.get('is_pinned', False)
        }).execute()
        return jsonify({"success": True, "post": response.data[0] if response.data else {}})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================
# API - FORUM REPLIES
# ============================================

@app.route('/api/forum-replies', methods=['GET'])
def get_forum_replies():
    """Get replies for a post"""
    try:
        post_id = request.args.get('post_id')
        if not post_id:
            return jsonify({"success": False, "error": "post_id required"}), 400
        
        response = supabase.table('forum_replies') \
            .select('*') \
            .eq('post_id', post_id) \
            .order('created_at', asc=True) \
            .execute()
        
        return jsonify({"success": True, "replies": response.data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/forum-replies', methods=['POST'])
def create_forum_reply():
    """Create a new forum reply"""
    try:
        data = request.get_json()
        response = supabase.table('forum_replies').insert({
            "post_id": data.get('post_id'),
            "user_id": data.get('user_id'),
            "content": data.get('content')
        }).execute()
        return jsonify({"success": True, "reply": response.data[0] if response.data else {}})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================
# API - ANNOUNCEMENTS
# ============================================

@app.route('/api/announcements', methods=['GET'])
def get_announcements():
    """Get announcements"""
    try:
        response = supabase.table('announcements') \
            .select('*') \
            .order('created_at', desc=True) \
            .execute()
        
        return jsonify({"success": True, "announcements": response.data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/announcements', methods=['POST'])
def create_announcement():
    """Create an announcement"""
    try:
        data = request.get_json()
        response = supabase.table('announcements').insert({
            "title": data.get('title'),
            "content": data.get('content'),
            "author_id": data.get('author_id'),
            "author_name": data.get('author_name', 'Admin'),
            "author_role": data.get('author_role', 'admin'),
            "target_type": data.get('target_type', 'all'),
            "is_pinned": data.get('is_pinned', False)
        }).execute()
        return jsonify({"success": True, "announcement": response.data[0] if response.data else {}})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/announcements/<announcement_id>', methods=['DELETE'])
def delete_announcement(announcement_id):
    """Delete an announcement"""
    try:
        supabase.table('announcements').delete().eq('id', announcement_id).execute()
        return jsonify({"success": True, "message": "Announcement deleted"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================
# API - RECORDINGS (Video Upload to Supabase Storage)
# ============================================

@app.route('/api/recordings/upload', methods=['POST'])
def upload_recording():
    """Upload a video recording to Supabase Storage"""
    try:
        if 'video' not in request.files:
            return jsonify({"success": False, "error": "No video file"}), 400
        
        file = request.files['video']
        if file.filename == '':
            return jsonify({"success": False, "error": "No file selected"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"success": False, "error": "File type not allowed"}), 400
        
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'mp4'
        filename = f"{uuid.uuid4()}.{file_extension}"
        
        # Read file content
        file_content = file.read()
        
        # Upload to Supabase Storage
        bucket_name = 'Videos'
        
        try:
            # Try to upload to Supabase Storage
            response = supabase.storage.from_(bucket_name).upload(
                filename,
                file_content,
                {"content-type": f"video/{file_extension}"}
            )
            
            # Get public URL
            public_url = supabase.storage.from_(bucket_name).get_public_url(filename)
            
        except Exception as storage_error:
            # If bucket doesn't exist, try to create it
            if "bucket not found" in str(storage_error).lower():
                # Create bucket
                supabase.storage.create_bucket(bucket_name, {"public": True})
                # Retry upload
                response = supabase.storage.from_(bucket_name).upload(
                    filename,
                    file_content,
                    {"content-type": f"video/{file_extension}"}
                )
                public_url = supabase.storage.from_(bucket_name).get_public_url(filename)
            else:
                raise storage_error
        
        # Get session_id from form data
        session_id = request.form.get('session_id')
        room_id = request.form.get('room_id')
        
        # Save to database
        if session_id:
            supabase.table('recorded_whiteboards').insert({
                "session_id": session_id,
                "room_id": room_id,
                "recording_url": public_url,
                "storage_path": filename,
                "recorded_at": datetime.datetime.now().isoformat(),
                "teacher_id": "teacher",
                "is_video": True
            }).execute()
        
        return jsonify({
            "success": True,
            "message": "Recording uploaded successfully",
            "filename": filename,
            "url": public_url
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/recordings/list', methods=['GET'])
def get_recordings():
    """Get list of recordings"""
    try:
        response = supabase.table('recorded_whiteboards') \
            .select('*, interactive_sessions(session_name)') \
            .order('recorded_at', desc=True) \
            .execute()
        
        return jsonify({
            "success": True,
            "recordings": response.data
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/recordings/<recording_id>', methods=['DELETE'])
def delete_recording(recording_id):
    """Delete a recording"""
    try:
        # Get recording info
        response = supabase.table('recorded_whiteboards') \
            .select('storage_path') \
            .eq('id', recording_id) \
            .execute()
        
        if response.data and response.data[0].get('storage_path'):
            # Delete from storage
            try:
                supabase.storage.from_('Videos').remove([response.data[0]['storage_path']])
            except:
                pass
        
        # Delete from database
        supabase.table('recorded_whiteboards').delete().eq('id', recording_id).execute()
        
        return jsonify({"success": True, "message": "Recording deleted"})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================
# API - GRADES
# ============================================

@app.route('/api/grades', methods=['GET'])
def get_grades():
    """Get grades for a student or class"""
    try:
        student_id = request.args.get('student_id')
        
        query = supabase.table('grades').select('*, students(full_name), subjects(name)')
        
        if student_id:
            query = query.eq('student_id', student_id)
        
        response = query.order('created_at', desc=True).execute()
        
        return jsonify({"success": True, "grades": response.data})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/grades', methods=['POST'])
def create_grade():
    """Create a new grade"""
    try:
        data = request.get_json()
        score = data.get('score')
        grade_letter = data.get('grade_letter')
        
        # Auto-calculate grade letter if not provided
        if score is not None and not grade_letter:
            if score >= 80:
                grade_letter = 'A'
            elif score >= 70:
                grade_letter = 'B'
            elif score >= 60:
                grade_letter = 'C'
            elif score >= 50:
                grade_letter = 'D'
            else:
                grade_letter = 'F'
        
        response = supabase.table('grades').insert({
            "student_id": data.get('student_id'),
            "subject_id": data.get('subject_id'),
            "score": score,
            "grade_letter": grade_letter,
            "term": data.get('term', 'Term 1'),
            "teacher_notes": data.get('teacher_notes'),
            "academic_year": data.get('academic_year', '2026')
        }).execute()
        
        return jsonify({"success": True, "grade": response.data[0] if response.data else {}})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================
# API - ATTENDANCE
# ============================================

@app.route('/api/attendance', methods=['POST'])
def mark_attendance():
    """Mark attendance for a student"""
    try:
        data = request.get_json()
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        
        # Check if already marked
        existing = supabase.table('attendance') \
            .select('id') \
            .eq('student_id', data.get('student_id')) \
            .eq('date', today) \
            .execute()
        
        if existing.data:
            # Update existing
            response = supabase.table('attendance') \
                .update({"status": data.get('status')}) \
                .eq('id', existing.data[0]['id']) \
                .execute()
        else:
            # Insert new
            response = supabase.table('attendance').insert({
                "student_id": data.get('student_id'),
                "date": today,
                "status": data.get('status')
            }).execute()
        
        return jsonify({"success": True, "message": "Attendance marked"})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/attendance/<student_id>', methods=['GET'])
def get_attendance(student_id):
    """Get attendance for a student"""
    try:
        response = supabase.table('attendance') \
            .select('*') \
            .eq('student_id', student_id) \
            .order('date', desc=True) \
            .execute()
        
        return jsonify({"success": True, "attendance": response.data})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================
# API - MESSAGES
# ============================================

@app.route('/api/messages', methods=['GET'])
def get_messages():
    """Get messages for a user"""
    try:
        user_id = request.args.get('user_id')
        class_id = request.args.get('class_id')
        
        if not user_id:
            return jsonify({"success": False, "error": "user_id required"}), 400
        
        query = supabase.table('messages') \
            .select('*') \
            .or_(f'sender_id.eq.{user_id},receiver_id.eq.{user_id}')
        
        if class_id:
            query = query.eq('class_id', class_id)
        
        response = query.order('created_at', desc=True).execute()
        
        return jsonify({"success": True, "messages": response.data})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/messages', methods=['POST'])
def send_message():
    """Send a message"""
    try:
        data = request.get_json()
        response = supabase.table('messages').insert({
            "sender_id": data.get('sender_id'),
            "sender_name": data.get('sender_name'),
            "sender_role": data.get('sender_role', 'student'),
            "receiver_id": data.get('receiver_id'),
            "receiver_role": data.get('receiver_role', 'teacher'),
            "class_id": data.get('class_id'),
            "message": data.get('message'),
            "is_read": False
        }).execute()
        
        return jsonify({"success": True, "message": response.data[0] if response.data else {}})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================
# API - FORMS & SUBJECTS (For Signup)
# ============================================

@app.route('/api/forms', methods=['GET'])
def get_forms():
    """Get all forms"""
    try:
        response = supabase.table('forms').select('*').order('name').execute()
        return jsonify({"success": True, "forms": response.data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/form-subjects/<form_id>', methods=['GET'])
def get_form_subjects(form_id):
    """Get subjects for a form"""
    try:
        response = supabase.table('form_subjects') \
            .select('subject_id, is_compulsory, is_optional, is_root, subjects(id, name, category)') \
            .eq('form_id', form_id) \
            .execute()
        
        return jsonify({"success": True, "subjects": response.data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================
# API - USERS (Admin)
# ============================================

@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all users (admin only)"""
    try:
        response = supabase.table('users').select('*').order('created_at', desc=True).execute()
        return jsonify({"success": True, "users": response.data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user"""
    try:
        # Get user data first
        user_response = supabase.table('users').select('auth_user_id').eq('id', user_id).execute()
        
        if user_response.data and user_response.data[0].get('auth_user_id'):
            # Try to delete from auth
            try:
                # This requires admin privileges - may not work with anon key
                pass
            except:
                pass
        
        # Delete from users table
        supabase.table('users').delete().eq('id', user_id).execute()
        
        return jsonify({"success": True, "message": "User deleted"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

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