# ============================================
# MEZANEYO SCHOOL - Flask Backend
# Using SQLAlchemy + PostgreSQL (Like your working app)
# ============================================

from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'c0b06cdcf564ac883d6a78948d560393cad025186db688573885f13c2a9f5565')
CORS(app, supports_credentials=True)

# ============================================
# DATABASE CONFIGURATION
# ============================================

database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

# Fallback to Supabase PostgreSQL if DATABASE_URL not set
if not database_url:
    database_url = 'postgresql://postgres:postgres@localhost:5432/mezaneyo'

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ============================================
# MODELS
# ============================================

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    auth_user_id = db.Column(db.String(36), unique=True, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='student')
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student_profile = db.relationship('Student', backref='user', lazy=True, uselist=False)
    teacher_profile = db.relationship('Teacher', backref='user', lazy=True, uselist=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    student_id_number = db.Column(db.String(50), unique=True, nullable=False)
    class_id = db.Column(db.String(36), nullable=True)
    guardian_name = db.Column(db.String(100))
    guardian_phone = db.Column(db.String(20))
    guardian_email = db.Column(db.String(120))
    date_of_birth = db.Column(db.Date)
    enrollment_date = db.Column(db.Date, default=datetime.utcnow)
    optional_subject_id = db.Column(db.String(36), nullable=True)
    root_id = db.Column(db.String(36), nullable=True)
    profile_picture_url = db.Column(db.String(500))

class Teacher(db.Model):
    __tablename__ = 'teachers'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    employee_id = db.Column(db.String(50), unique=True)
    subject_specialty = db.Column(db.String(100))
    hire_date = db.Column(db.Date, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    profile_picture_url = db.Column(db.String(500))

class Form(db.Model):
    __tablename__ = 'forms'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(20), unique=True, nullable=False)  # Form 1, Form 2, etc.

class Subject(db.Model):
    __tablename__ = 'subjects'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), unique=True, nullable=False)
    category = db.Column(db.String(20), default='compulsory')  # compulsory, optional, root

class Class(db.Model):
    __tablename__ = 'classes'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    form_id = db.Column(db.String(36), db.ForeignKey('forms.id'))
    class_name = db.Column(db.String(50), nullable=False)
    class_teacher_id = db.Column(db.String(36), db.ForeignKey('teachers.id'))
    academic_year = db.Column(db.String(20), default='2026')

class Lesson(db.Model):
    __tablename__ = 'lessons'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    teacher_id = db.Column(db.String(36), db.ForeignKey('teachers.id'))
    class_id = db.Column(db.String(36), db.ForeignKey('classes.id'))
    subject_id = db.Column(db.String(36), db.ForeignKey('subjects.id'))
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    lesson_type = db.Column(db.String(20), default='text')
    video_url = db.Column(db.String(500))
    attachments = db.Column(db.JSON)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Assignment(db.Model):
    __tablename__ = 'assignments'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    teacher_id = db.Column(db.String(36), db.ForeignKey('teachers.id'))
    class_id = db.Column(db.String(36), db.ForeignKey('classes.id'))
    subject_id = db.Column(db.String(36), db.ForeignKey('subjects.id'))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.Date, nullable=False)
    attachment_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Grade(db.Model):
    __tablename__ = 'grades'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = db.Column(db.String(36), db.ForeignKey('students.id'))
    subject_id = db.Column(db.String(36), db.ForeignKey('subjects.id'))
    score = db.Column(db.Float)
    grade_letter = db.Column(db.String(2))
    term = db.Column(db.String(20), default='Term 1')
    teacher_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Attendance(db.Model):
    __tablename__ = 'attendance'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = db.Column(db.String(36), db.ForeignKey('students.id'))
    date = db.Column(db.Date, default=datetime.utcnow)
    status = db.Column(db.String(20), default='present')  # present, absent, late, excused

class Announcement(db.Model):
    __tablename__ = 'announcements'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    author_name = db.Column(db.String(100))
    author_role = db.Column(db.String(20))
    target_type = db.Column(db.String(20), default='all')
    is_pinned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Forum(db.Model):
    __tablename__ = 'forums'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    class_id = db.Column(db.String(36), db.ForeignKey('classes.id'))
    teacher_id = db.Column(db.String(36), db.ForeignKey('teachers.id'))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ForumPost(db.Model):
    __tablename__ = 'forum_posts'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    forum_id = db.Column(db.String(36), db.ForeignKey('forums.id'))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    content = db.Column(db.Text, nullable=False)
    is_pinned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ForumReply(db.Model):
    __tablename__ = 'forum_replies'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id = db.Column(db.String(36), db.ForeignKey('forum_posts.id'))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sender_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    receiver_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    class_id = db.Column(db.String(36), db.ForeignKey('classes.id'))
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class RecordedWhiteboard(db.Model):
    __tablename__ = 'recorded_whiteboards'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.String(36))
    room_id = db.Column(db.String(100))
    recording_url = db.Column(db.String(500))
    is_video = db.Column(db.Boolean, default=True)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# ============================================
# ROUTES - AUTHENTICATION
# ============================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    data = request.get_json() or request.form
    email = data.get('email')
    password = data.get('password')
    
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401
    
    login_user(user)
    session['user'] = {
        'id': user.id,
        'email': user.email,
        'full_name': user.full_name,
        'role': user.role
    }
    
    return jsonify({
        "success": True,
        "message": "Login successful!",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role
        }
    })

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('index'))

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')
    role = data.get('role', 'student')
    
    if not all([email, password, full_name]):
        return jsonify({"error": "All fields are required"}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 400
    
    user = User(email=email, full_name=full_name, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    # Create student or teacher profile
    if role == 'student':
        student = Student(
            user_id=user.id,
            student_id_number=f"MEZ-{datetime.now().year}-{str(uuid.uuid4())[:6].upper()}"
        )
        db.session.add(student)
    elif role == 'teacher':
        teacher = Teacher(
            user_id=user.id,
            employee_id=f"TCH-{str(uuid.uuid4())[:6].upper()}"
        )
        db.session.add(teacher)
    
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "Registration successful! Please login.",
        "user_id": user.id
    })

@app.route('/api/auth/me', methods=['GET'])
def get_current_user():
    if 'user' in session:
        return jsonify({"success": True, "user": session['user']})
    return jsonify({"success": False, "error": "Not logged in"}), 401

@app.route('/api/auth/logout', methods=['POST'])
def api_logout():
    logout_user()
    session.clear()
    return jsonify({"success": True, "message": "Logged out"})

# ============================================
# ROUTES - DASHBOARDS
# ============================================

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
# API ROUTES - STUDENTS
# ============================================

@app.route('/api/students', methods=['GET'])
@login_required
def get_students():
    if current_user.role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403
    
    students = Student.query.all()
    return jsonify({
        "success": True,
        "students": [{
            "id": s.id,
            "full_name": s.user.full_name,
            "student_id_number": s.student_id_number,
            "guardian_name": s.guardian_name,
            "guardian_phone": s.guardian_phone
        } for s in students]
    })

@app.route('/api/students', methods=['POST'])
@login_required
def create_student():
    if current_user.role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.get_json()
    full_name = data.get('full_name')
    email = data.get('email')
    student_id = data.get('student_id_number')
    password = data.get('password', 'password123')
    
    # Create user
    user = User(email=email, full_name=full_name, role='student')
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    
    # Create student
    student = Student(
        user_id=user.id,
        student_id_number=student_id or f"MEZ-{datetime.now().year}-{str(uuid.uuid4())[:6].upper()}",
        guardian_name=data.get('guardian_name'),
        guardian_phone=data.get('guardian_phone'),
        guardian_email=data.get('guardian_email')
    )
    db.session.add(student)
    db.session.commit()
    
    return jsonify({"success": True, "student": {"id": student.id, "full_name": full_name}})

# ============================================
# CREATE TABLES
# ============================================

with app.app_context():
    db.create_all()
    print("✅ Database tables created!")

# ============================================
# RUN
# ============================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
