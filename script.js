// =============================================
// MEZANEYO SCHOOL - MODULAR ENHANCEMENT SCRIPT
// =============================================

// =============================================
// SUPABASE CONFIG
// =============================================
//const SUPABASE_URL = 'https://nivmrwbusbeppdssmfpj.supabase.co';
//const SUPABASE_ANON_KEY = 'sb_publishable_kwF_yAmJ5AWnbaIe57snrw_fXng7-6a';
//const supabaseClient = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// =============================================
// FEATURE: REAL-TIME NOTIFICATIONS
// =============================================
class NotificationManager {
    constructor() {
        this.notifications = [];
        this.listeners = [];
    }

    // Add notification
    add(notification) {
        this.notifications.unshift({
            id: Date.now(),
            read: false,
            timestamp: new Date().toISOString(),
            ...notification
        });
        this.notifyListeners();
        this.showToast(notification.message, notification.type);
    }

    // Get all notifications
    getAll() {
        return this.notifications;
    }

    // Get unread count
    getUnreadCount() {
        return this.notifications.filter(n => !n.read).length;
    }

    // Mark as read
    markAsRead(id) {
        const notif = this.notifications.find(n => n.id === id);
        if (notif) notif.read = true;
        this.notifyListeners();
    }

    // Mark all as read
    markAllAsRead() {
        this.notifications.forEach(n => n.read = true);
        this.notifyListeners();
    }

    // Subscribe to changes
    subscribe(callback) {
        this.listeners.push(callback);
    }

    // Notify listeners
    notifyListeners() {
        this.listeners.forEach(cb => cb(this.notifications));
    }

    // Show toast
    showToast(message, type = 'info') {
        const existing = document.querySelector('.toast-notification');
        if (existing) existing.remove();

        const colors = {
            success: '#28a745',
            error: '#dc3545',
            warning: '#ffc107',
            info: '#007bff'
        };

        const toast = document.createElement('div');
        toast.className = 'toast-notification';
        toast.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 12px 24px;
            background: ${colors[type] || colors.info};
            color: white;
            border-radius: 8px;
            font-family: 'Poppins', sans-serif;
            font-size: 14px;
            z-index: 9999;
            max-width: 400px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            animation: slideInRight 0.4s ease forwards;
            cursor: pointer;
        `;
        toast.textContent = message;
        toast.onclick = () => {
            if (toast.parentNode) toast.remove();
        };
        document.body.appendChild(toast);

        setTimeout(() => {
            if (toast.parentNode) {
                toast.style.animation = 'slideOutRight 0.4s ease forwards';
                setTimeout(() => {
                    if (toast.parentNode) toast.remove();
                }, 400);
            }
        }, 4000);
    }
}

// Create global notification manager
const notifications = new NotificationManager();

// =============================================
// FEATURE: STUDENT ACTIVITY TRACKER
// =============================================
class StudentActivityTracker {
    constructor() {
        this.studentId = null;
        this.classId = null;
    }

    // Initialize with student data
    init(studentId, classId) {
        this.studentId = studentId;
        this.classId = classId;
    }

    // Track lesson view
    async trackLessonView(lessonId) {
        try {
            const { error } = await supabaseClient
                .from('lesson_progress')
                .upsert({
                    student_id: this.studentId,
                    lesson_id: lessonId,
                    viewed_at: new Date().toISOString(),
                    watched_percentage: 100
                }, { onConflict: 'student_id, lesson_id' });
            
            if (error) throw error;
            return true;
        } catch (error) {
            console.error('Error tracking lesson:', error);
            return false;
        }
    }

    // Track assignment submission
    async trackAssignment(assignmentId, submission) {
        try {
            const { error } = await supabaseClient
                .from('submissions')
                .insert({
                    assignment_id: assignmentId,
                    student_id: this.studentId,
                    submission_url: submission,
                    submitted_at: new Date().toISOString()
                });
            
            if (error) throw error;
            notifications.add({
                message: '✅ Assignment submitted successfully!',
                type: 'success'
            });
            return true;
        } catch (error) {
            console.error('Error submitting assignment:', error);
            return false;
        }
    }

    // Track quiz completion
    async trackQuiz(quizId, answers, score) {
        try {
            const { error } = await supabaseClient
                .from('quiz_attempts')
                .insert({
                    quiz_id: quizId,
                    student_id: this.studentId,
                    answers: answers,
                    score: score,
                    attempted_at: new Date().toISOString()
                });
            
            if (error) throw error;
            notifications.add({
                message: `📊 Quiz completed! Score: ${score}%`,
                type: score >= 70 ? 'success' : 'warning'
            });
            return true;
        } catch (error) {
            console.error('Error tracking quiz:', error);
            return false;
        }
    }
}

// =============================================
// FEATURE: TEACHER ANALYTICS
// =============================================
class TeacherAnalytics {
    constructor() {
        this.teacherId = null;
        this.classId = null;
    }

    // Initialize with teacher data
    init(teacherId, classId) {
        this.teacherId = teacherId;
        this.classId = classId;
    }

    // Get class performance summary
    async getClassPerformance() {
        try {
            // Get all students in class
            const { data: students } = await supabaseClient
                .from('students')
                .select('id, full_name')
                .eq('class_id', this.classId);

            if (!students || students.length === 0) {
                return { students: [], averages: {} };
            }

            // Get grades for each student
            const studentIds = students.map(s => s.id);
            const { data: grades } = await supabaseClient
                .from('grades')
                .select('*')
                .in('student_id', studentIds);

            // Calculate averages
            const studentAverages = {};
            const subjectAverages = {};

            students.forEach(s => {
                const studentGrades = grades.filter(g => g.student_id === s.id);
                const scores = studentGrades.map(g => g.score || 0);
                studentAverages[s.id] = scores.length > 0 ? 
                    Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : 0;
            });

            // Subject averages
            const subjectGroups = {};
            grades.forEach(g => {
                if (!subjectGroups[g.subject]) subjectGroups[g.subject] = [];
                subjectGroups[g.subject].push(g.score || 0);
            });
            Object.keys(subjectGroups).forEach(subject => {
                const scores = subjectGroups[subject];
                subjectAverages[subject] = Math.round(
                    scores.reduce((a, b) => a + b, 0) / scores.length
                );
            });

            return {
                students: students.map(s => ({
                    ...s,
                    average: studentAverages[s.id] || 0
                })),
                subjectAverages: subjectAverages,
                totalStudents: students.length
            };
        } catch (error) {
            console.error('Error getting class performance:', error);
            return { students: [], subjectAverages: {}, totalStudents: 0 };
        }
    }

    // Get attendance summary
    async getAttendanceSummary() {
        try {
            const today = new Date().toISOString().split('T')[0];
            const { data: attendance } = await supabaseClient
                .from('attendance')
                .select('*')
                .eq('class_id', this.classId)
                .eq('date', today);

            const present = attendance?.filter(a => a.status === 'present').length || 0;
            const total = attendance?.length || 1;

            return {
                present: present,
                absent: total - present,
                total: total,
                rate: Math.round((present / total) * 100)
            };
        } catch (error) {
            console.error('Error getting attendance:', error);
            return { present: 0, absent: 0, total: 0, rate: 0 };
        }
    }

    // Get assignment completion
    async getAssignmentCompletion() {
        try {
            const { data: assignments } = await supabaseClient
                .from('assignments')
                .select('id, title')
                .eq('teacher_id', this.teacherId);

            if (!assignments || assignments.length === 0) {
                return { assignments: [], completionRate: 0 };
            }

            const assignmentIds = assignments.map(a => a.id);
            const { data: submissions } = await supabaseClient
                .from('submissions')
                .select('assignment_id')
                .in('assignment_id', assignmentIds);

            const submissionCounts = {};
            assignmentIds.forEach(id => {
                submissionCounts[id] = submissions?.filter(s => s.assignment_id === id).length || 0;
            });

            return {
                assignments: assignments.map(a => ({
                    ...a,
                    submissions: submissionCounts[a.id] || 0
                })),
                completionRate: assignments.length > 0 ?
                    Math.round(
                        (Object.values(submissionCounts).reduce((a, b) => a + b, 0) / 
                        (assignments.length * 5)) * 100
                    ) : 0
            };
        } catch (error) {
            console.error('Error getting assignment completion:', error);
            return { assignments: [], completionRate: 0 };
        }
    }
}

// =============================================
// FEATURE: LIVE CLASS SCHEDULER
// =============================================
class LiveClassScheduler {
    constructor() {
        this.teacherId = null;
    }

    init(teacherId) {
        this.teacherId = teacherId;
    }

    // Schedule a live class
    async scheduleLiveClass(data) {
        try {
            const { error } = await supabaseClient
                .from('live_classes')
                .insert({
                    teacher_id: this.teacherId,
                    class_id: data.classId,
                    subject_id: data.subjectId,
                    title: data.title,
                    description: data.description || '',
                    scheduled_at: data.scheduledAt,
                    duration: data.duration || 60,
                    is_active: false
                });
            
            if (error) throw error;
            notifications.add({
                message: '📅 Live class scheduled successfully!',
                type: 'success'
            });
            return true;
        } catch (error) {
            console.error('Error scheduling live class:', error);
            notifications.add({
                message: '❌ Error scheduling live class',
                type: 'error'
            });
            return false;
        }
    }

    // Get upcoming live classes
    async getUpcomingClasses() {
        try {
            const { data, error } = await supabaseClient
                .from('live_classes')
                .select('*, classes(class_name), subjects(name)')
                .eq('teacher_id', this.teacherId)
                .gte('scheduled_at', new Date().toISOString())
                .order('scheduled_at', { ascending: true })
                .limit(5);
            
            if (error) throw error;
            return data || [];
        } catch (error) {
            console.error('Error getting upcoming classes:', error);
            return [];
        }
    }

    // Get past live classes (recordings)
    async getPastClasses() {
        try {
            const { data, error } = await supabaseClient
                .from('live_classes')
                .select('*, classes(class_name), subjects(name)')
                .eq('teacher_id', this.teacherId)
                .lt('scheduled_at', new Date().toISOString())
                .order('scheduled_at', { ascending: false })
                .limit(10);
            
            if (error) throw error;
            return data || [];
        } catch (error) {
            console.error('Error getting past classes:', error);
            return [];
        }
    }
}

// =============================================
// FEATURE: RESOURCE LIBRARY
// =============================================
class ResourceLibrary {
    constructor() {
        this.teacherId = null;
    }

    init(teacherId) {
        this.teacherId = teacherId;
    }

    // Upload resource
    async uploadResource(data) {
        try {
            const { error } = await supabaseClient
                .from('lesson_materials')
                .insert({
                    teacher_id: this.teacherId,
                    class_id: data.classId,
                    subject_id: data.subjectId,
                    title: data.title,
                    material_type: data.type || 'file',
                    material_url: data.url,
                    file_name: data.fileName || null,
                    file_size: data.fileSize || null
                });
            
            if (error) throw error;
            notifications.add({
                message: '📤 Resource uploaded successfully!',
                type: 'success'
            });
            return true;
        } catch (error) {
            console.error('Error uploading resource:', error);
            notifications.add({
                message: '❌ Error uploading resource',
                type: 'error'
            });
            return false;
        }
    }

    // Get resources for class
    async getResources(classId) {
        try {
            const { data, error } = await supabaseClient
                .from('lesson_materials')
                .select('*')
                .eq('class_id', classId)
                .order('created_at', { ascending: false });
            
            if (error) throw error;
            return data || [];
        } catch (error) {
            console.error('Error getting resources:', error);
            return [];
        }
    }

    // Delete resource
    async deleteResource(resourceId) {
        try {
            const { error } = await supabaseClient
                .from('lesson_materials')
                .delete()
                .eq('id', resourceId);
            
            if (error) throw error;
            notifications.add({
                message: '🗑️ Resource deleted',
                type: 'info'
            });
            return true;
        } catch (error) {
            console.error('Error deleting resource:', error);
            return false;
        }
    }
}

// =============================================
// FEATURE: DISCUSSION FORUM ENHANCER
// =============================================
class ForumEnhancer {
    constructor() {
        this.forumId = null;
    }

    init(forumId) {
        this.forumId = forumId;
    }

    // Get forum stats
    async getStats() {
        try {
            const { count: posts } = await supabaseClient
                .from('forum_posts')
                .select('*', { count: 'exact', head: true })
                .eq('forum_id', this.forumId);

            const { count: replies } = await supabaseClient
                .from('forum_replies')
                .select('*', { count: 'exact', head: true })
                .eq('forum_id', this.forumId);

            return {
                posts: posts || 0,
                replies: replies || 0,
                total: (posts || 0) + (replies || 0)
            };
        } catch (error) {
            console.error('Error getting forum stats:', error);
            return { posts: 0, replies: 0, total: 0 };
        }
    }

    // Get most active users
    async getActiveUsers() {
        try {
            // Get posts by user
            const { data: posts } = await supabaseClient
                .from('forum_posts')
                .select('user_id, user_name')
                .eq('forum_id', this.forumId);

            // Get replies by user
            const { data: replies } = await supabaseClient
                .from('forum_replies')
                .select('user_id')
                .eq('forum_id', this.forumId);

            // Count activity
            const activity = {};
            posts?.forEach(p => {
                activity[p.user_id] = (activity[p.user_id] || 0) + 1;
            });
            replies?.forEach(r => {
                activity[r.user_id] = (activity[r.user_id] || 0) + 1;
            });

            // Sort by activity
            const sorted = Object.entries(activity)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 5)
                .map(([userId, count]) => ({
                    userId,
                    userName: posts?.find(p => p.user_id === userId)?.user_name || 'User',
                    activity: count
                }));

            return sorted;
        } catch (error) {
            console.error('Error getting active users:', error);
            return [];
        }
    }
}

// =============================================
// FEATURE: ASSIGNMENT GRADER
// =============================================
class AssignmentGrader {
    constructor() {
        this.teacherId = null;
    }

    init(teacherId) {
        this.teacherId = teacherId;
    }

    // Grade an assignment
    async gradeAssignment(submissionId, score, feedback) {
        try {
            const { error } = await supabaseClient
                .from('submissions')
                .update({
                    score: score,
                    feedback: feedback,
                    graded_at: new Date().toISOString()
                })
                .eq('id', submissionId);
            
            if (error) throw error;
            notifications.add({
                message: `✅ Assignment graded: ${score}%`,
                type: 'success'
            });
            return true;
        } catch (error) {
            console.error('Error grading assignment:', error);
            notifications.add({
                message: '❌ Error grading assignment',
                type: 'error'
            });
            return false;
        }
    }

    // Get pending submissions
    async getPendingSubmissions(classId) {
        try {
            const { data, error } = await supabaseClient
                .from('submissions')
                .select('*, assignments(title), students(full_name)')
                .eq('class_id', classId)
                .is('score', null)
                .order('submitted_at', { ascending: true });
            
            if (error) throw error;
            return data || [];
        } catch (error) {
            console.error('Error getting pending submissions:', error);
            return [];
        }
    }

    // Get graded submissions
    async getGradedSubmissions(classId) {
        try {
            const { data, error } = await supabaseClient
                .from('submissions')
                .select('*, assignments(title), students(full_name)')
                .eq('class_id', classId)
                .not('score', 'is', null)
                .order('graded_at', { ascending: false })
                .limit(20);
            
            if (error) throw error;
            return data || [];
        } catch (error) {
            console.error('Error getting graded submissions:', error);
            return [];
        }
    }
}

// =============================================
// FEATURE: ANNOUNCEMENT BROADCASTER
// =============================================
class AnnouncementBroadcaster {
    constructor() {
        this.adminId = null;
    }

    init(adminId) {
        this.adminId = adminId;
    }

    // Broadcast announcement
    async broadcast(data) {
        try {
            const { error } = await supabaseClient
                .from('announcements')
                .insert({
                    title: data.title,
                    content: data.content,
                    author_id: this.adminId,
                    author_name: data.authorName || 'Admin',
                    author_role: 'admin',
                    target_type: data.target || 'all',
                    is_pinned: data.pinned || false
                });
            
            if (error) throw error;
            notifications.add({
                message: '📢 Announcement broadcasted!',
                type: 'success'
            });
            return true;
        } catch (error) {
            console.error('Error broadcasting announcement:', error);
            notifications.add({
                message: '❌ Error broadcasting announcement',
                type: 'error'
            });
            return false;
        }
    }

    // Get all announcements
    async getAllAnnouncements() {
        try {
            const { data, error } = await supabaseClient
                .from('announcements')
                .select('*')
                .order('created_at', { ascending: false });
            
            if (error) throw error;
            return data || [];
        } catch (error) {
            console.error('Error getting announcements:', error);
            return [];
        }
    }

    // Delete announcement
    async deleteAnnouncement(announcementId) {
        try {
            const { error } = await supabaseClient
                .from('announcements')
                .delete()
                .eq('id', announcementId);
            
            if (error) throw error;
            notifications.add({
                message: '🗑️ Announcement deleted',
                type: 'info'
            });
            return true;
        } catch (error) {
            console.error('Error deleting announcement:', error);
            return false;
        }
    }
}

// =============================================
// EXPOSE ALL CLASSES AND FUNCTIONS
// =============================================

// Global instances
window.notifications = notifications;
window.StudentActivityTracker = StudentActivityTracker;
window.TeacherAnalytics = TeacherAnalytics;
window.LiveClassScheduler = LiveClassScheduler;
window.ResourceLibrary = ResourceLibrary;
window.ForumEnhancer = ForumEnhancer;
window.AssignmentGrader = AssignmentGrader;
window.AnnouncementBroadcaster = AnnouncementBroadcaster;

// Supabase client
window.supabaseClient = supabaseClient;

// Console log to confirm loaded
console.log('✅ MEZANEYO Enhancement Script Loaded');