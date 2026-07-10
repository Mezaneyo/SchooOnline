# ============================================
# MEZANEYO SCHOOL - Flask Backend
# Using SQLAlchemy + PostgreSQL
# ============================================

from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import uuid
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'c0b06cdcf564ac883d6a78948d560393cad025186db688573885f13c2a9f5565')
CORS(app, supports_credentials=True)

# ============================================
# DATABASE CONFIGURATION
# ============================================

database_url = os.environ.get('DATABASE_URL')
if not database_url:
    print("❌ DATABASE_URL not set!", file=sys.stderr)
    # Use SQLite as fallback for testing
    database_url = 'sqlite:///mezaneyo.db'
    print("⚠️ Using SQLite fallback", file=sys.stderr)

if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ============================================
# MODELS (Simplified for testing)
# ============================================

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='student')
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    student_id_number = db.Column(db.String(50), unique=True)
    class_id = db.Column(db.String(36))
    guardian_name = db.Column(db.String(100))
    guardian_phone = db.Column(db.String(20))

class Teacher(db.Model):
    __tablename__ = 'teachers'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    employee_id = db.Column(db.String(50), unique=True)
    subject_specialty = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)

class Announcement(db.Model):
    __tablename__ = 'announcements'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.String(36))
    author_name = db.Column(db.String(100))
    is_pinned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
    
    try:
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
            "user": session['user']
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('index'))

@app.route('/register', methods=['POST'])
def register():
    try:
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
        
        # Create profile
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
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
# API ROUTES
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
            "full_name": s.user.full_name if s.user else "Unknown",
            "student_id_number": s.student_id_number,
            "guardian_name": s.guardian_name,
            "guardian_phone": s.guardian_phone
        } for s in students]
    })

@app.route('/api/announcements', methods=['GET'])
def get_announcements():
    try:
        announcements = Announcement.query.order_by(Announcement.created_at.desc()).limit(10).all()
        return jsonify({
            "success": True,
            "announcements": [{
                "id": a.id,
                "title": a.title,
                "content": a.content,
                "author_name": a.author_name,
                "is_pinned": a.is_pinned,
                "created_at": a.created_at.isoformat() if a.created_at else None
            } for a in announcements]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "connected" if database_url else "not configured"
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
# CREATE TABLES
# ============================================

@app.before_first_request
def create_tables():
    db.create_all()
    print("✅ Database tables created!")

# ============================================
# RUN
# ============================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
