from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, jsonify
import sqlite3
import os
import io
import base64
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER

app = Flask(__name__)
app.secret_key = 'nayepankh_secret_2024'

DB = 'nayepankh.db'

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'volunteer',
            phone TEXT,
            city TEXT,
            skills TEXT,
            bio TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL,
            location TEXT,
            max_volunteers INTEGER DEFAULT 50,
            created_by INTEGER,
            status TEXT DEFAULT 'upcoming',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS event_registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER,
            user_id INTEGER,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(event_id) REFERENCES events(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS internship_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            domain TEXT NOT NULL,
            duration TEXT,
            motivation TEXT,
            experience TEXT,
            status TEXT DEFAULT 'pending',
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS donations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            donor_name TEXT NOT NULL,
            email TEXT,
            amount REAL NOT NULL,
            purpose TEXT,
            payment_mode TEXT,
            donated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message TEXT,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
    ''')
    # Seed admin
    try:
        c.execute("INSERT INTO users (name,email,password,role,status) VALUES (?,?,?,?,?)",
                  ('Admin', 'admin@nayepankh.org', generate_password_hash('admin123'), 'admin', 'active'))
    except:
        pass
    # Seed sample data
    try:
        c.execute("INSERT INTO events (title,description,date,location,max_volunteers,created_by) VALUES (?,?,?,?,?,?)",
                  ('Tree Plantation Drive', 'Plant 500 trees in the community park.', '2025-02-15', 'Delhi', 100, 1))
        c.execute("INSERT INTO events (title,description,date,location,max_volunteers,created_by) VALUES (?,?,?,?,?,?)",
                  ('Blood Donation Camp', 'Annual blood donation event.', '2025-03-10', 'Mumbai', 80, 1))
        c.execute("INSERT INTO donations (donor_name,email,amount,purpose,payment_mode) VALUES (?,?,?,?,?)",
                  ('Rahul Sharma', 'rahul@example.com', 5000, 'Education', 'UPI'))
        c.execute("INSERT INTO donations (donor_name,email,amount,purpose,payment_mode) VALUES (?,?,?,?,?)",
                  ('Priya Mehta', 'priya@example.com', 10000, 'Healthcare', 'Bank Transfer'))
    except:
        pass
    conn.commit()
    conn.close()

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated

def add_notification(user_id, message):
    conn = get_db()
    conn.execute("INSERT INTO notifications (user_id, message) VALUES (?,?)", (user_id, message))
    conn.commit()
    conn.close()

# ─── ROUTES ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    conn = get_db()
    volunteer_count = conn.execute("SELECT COUNT(*) FROM users WHERE role='volunteer' AND status='active'").fetchone()[0]
    event_count = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    donation_total = conn.execute("SELECT COALESCE(SUM(amount),0) FROM donations").fetchone()[0]
    intern_count = conn.execute("SELECT COUNT(*) FROM users WHERE role='intern' AND status='active'").fetchone()[0]
    events = conn.execute("SELECT * FROM events ORDER BY date DESC LIMIT 3").fetchall()
    conn.close()
    return render_template('index.html',
        volunteer_count=volunteer_count, event_count=event_count,
        donation_total=int(donation_total), intern_count=intern_count, events=events)

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', 'volunteer')
        phone = request.form.get('phone', '')
        city = request.form.get('city', '')
        skills = request.form.get('skills', '')
        conn = get_db()
        try:
            conn.execute("INSERT INTO users (name,email,password,role,phone,city,skills) VALUES (?,?,?,?,?,?,?)",
                         (name, email, generate_password_hash(password), role, phone, city, skills))
            conn.commit()
            flash('Registration successful! Await admin approval.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already registered.', 'danger')
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            if user['status'] == 'pending':
                flash('Your account is pending approval.', 'warning')
                return redirect(url_for('login'))
            session['user_id'] = user['id']
            session['name'] = user['name']
            session['role'] = user['role']
            flash(f'Welcome back, {user["name"]}!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db()
    uid = session['user_id']
    role = session['role']
    stats = {}
    if role == 'admin':
        stats['volunteers'] = conn.execute("SELECT COUNT(*) FROM users WHERE role='volunteer'").fetchone()[0]
        stats['interns'] = conn.execute("SELECT COUNT(*) FROM users WHERE role='intern'").fetchone()[0]
        stats['events'] = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        stats['donations'] = conn.execute("SELECT COALESCE(SUM(amount),0) FROM donations").fetchone()[0]
        stats['pending'] = conn.execute("SELECT COUNT(*) FROM users WHERE status='pending'").fetchone()[0]
        stats['applications'] = conn.execute("SELECT COUNT(*) FROM internship_applications WHERE status='pending'").fetchone()[0]
        recent_users = conn.execute("SELECT * FROM users ORDER BY created_at DESC LIMIT 5").fetchall()
        recent_donations = conn.execute("SELECT * FROM donations ORDER BY donated_at DESC LIMIT 5").fetchall()
        conn.close()
        return render_template('dashboard.html', stats=stats, recent_users=recent_users, recent_donations=recent_donations)
    else:
        my_events = conn.execute("""SELECT e.* FROM events e 
            JOIN event_registrations r ON e.id=r.event_id WHERE r.user_id=?""", (uid,)).fetchall()
        my_app = conn.execute("SELECT * FROM internship_applications WHERE user_id=? ORDER BY applied_at DESC LIMIT 1", (uid,)).fetchone()
        notifs = conn.execute("SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC LIMIT 5", (uid,)).fetchall()
        conn.close()
        return render_template('dashboard.html', my_events=my_events, my_app=my_app, notifs=notifs)

# ─── VOLUNTEERS ─────────────────────────────────────────────────────────────────

@app.route('/volunteers')
@login_required
def volunteers():
    conn = get_db()
    q = request.args.get('q', '')
    status_filter = request.args.get('status', '')
    query = "SELECT * FROM users WHERE role='volunteer'"
    params = []
    if q:
        query += " AND (name LIKE ? OR email LIKE ? OR city LIKE ?)"
        params += [f'%{q}%', f'%{q}%', f'%{q}%']
    if status_filter:
        query += " AND status=?"
        params.append(status_filter)
    query += " ORDER BY created_at DESC"
    volunteers = conn.execute(query, params).fetchall()
    conn.close()
    return render_template('volunteers.html', volunteers=volunteers, q=q, status_filter=status_filter)

@app.route('/volunteers/approve/<int:uid>', methods=['POST'])
@login_required
@admin_required
def approve_volunteer(uid):
    conn = get_db()
    conn.execute("UPDATE users SET status='active' WHERE id=?", (uid,))
    conn.commit()
    add_notification(uid, 'Your volunteer account has been approved! Welcome to NayePankh.')
    conn.close()
    flash('Volunteer approved.', 'success')
    return redirect(url_for('volunteers'))

@app.route('/volunteers/reject/<int:uid>', methods=['POST'])
@login_required
@admin_required
def reject_volunteer(uid):
    conn = get_db()
    conn.execute("UPDATE users SET status='rejected' WHERE id=?", (uid,))
    conn.commit()
    conn.close()
    flash('Volunteer rejected.', 'warning')
    return redirect(url_for('volunteers'))

@app.route('/volunteers/delete/<int:uid>', methods=['POST'])
@login_required
@admin_required
def delete_volunteer(uid):
    conn = get_db()
    conn.execute("DELETE FROM users WHERE id=?", (uid,))
    conn.commit()
    conn.close()
    flash('Volunteer deleted.', 'danger')
    return redirect(url_for('volunteers'))

@app.route('/volunteers/edit/<int:uid>', methods=['GET','POST'])
@login_required
@admin_required
def edit_volunteer(uid):
    conn = get_db()
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        city = request.form['city']
        skills = request.form['skills']
        status = request.form['status']
        conn.execute("UPDATE users SET name=?,phone=?,city=?,skills=?,status=? WHERE id=?",
                     (name, phone, city, skills, status, uid))
        conn.commit()
        conn.close()
        flash('Volunteer updated.', 'success')
        return redirect(url_for('volunteers'))
    user = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    conn.close()
    return render_template('edit_volunteer.html', user=user)

# ─── EVENTS ─────────────────────────────────────────────────────────────────────

@app.route('/events')
@login_required
def events():
    conn = get_db()
    q = request.args.get('q', '')
    query = "SELECT * FROM events"
    params = []
    if q:
        query += " WHERE title LIKE ? OR location LIKE ?"
        params = [f'%{q}%', f'%{q}%']
    query += " ORDER BY date DESC"
    events = conn.execute(query, params).fetchall()
    registered = []
    if session.get('user_id'):
        regs = conn.execute("SELECT event_id FROM event_registrations WHERE user_id=?", (session['user_id'],)).fetchall()
        registered = [r['event_id'] for r in regs]
    conn.close()
    return render_template('events.html', events=events, registered=registered, q=q)

@app.route('/events/create', methods=['GET','POST'])
@login_required
@admin_required
def create_event():
    if request.method == 'POST':
        title = request.form['title']
        desc = request.form['description']
        date = request.form['date']
        location = request.form['location']
        max_v = request.form.get('max_volunteers', 50)
        conn = get_db()
        conn.execute("INSERT INTO events (title,description,date,location,max_volunteers,created_by) VALUES (?,?,?,?,?,?)",
                     (title, desc, date, location, max_v, session['user_id']))
        conn.commit()
        conn.close()
        flash('Event created!', 'success')
        return redirect(url_for('events'))
    return render_template('create_event.html')

@app.route('/events/register/<int:eid>', methods=['POST'])
@login_required
def register_event(eid):
    conn = get_db()
    existing = conn.execute("SELECT * FROM event_registrations WHERE event_id=? AND user_id=?",
                            (eid, session['user_id'])).fetchone()
    if existing:
        flash('Already registered for this event.', 'info')
    else:
        conn.execute("INSERT INTO event_registrations (event_id, user_id) VALUES (?,?)",
                     (eid, session['user_id']))
        conn.commit()
        flash('Registered for event!', 'success')
    conn.close()
    return redirect(url_for('events'))

@app.route('/events/delete/<int:eid>', methods=['POST'])
@login_required
@admin_required
def delete_event(eid):
    conn = get_db()
    conn.execute("DELETE FROM events WHERE id=?", (eid,))
    conn.execute("DELETE FROM event_registrations WHERE event_id=?", (eid,))
    conn.commit()
    conn.close()
    flash('Event deleted.', 'danger')
    return redirect(url_for('events'))

# ─── INTERNSHIPS ─────────────────────────────────────────────────────────────────

@app.route('/internships')
@login_required
def internships():
    conn = get_db()
    if session['role'] == 'admin':
        apps = conn.execute("""SELECT ia.*, u.name, u.email FROM internship_applications ia
            JOIN users u ON ia.user_id=u.id ORDER BY ia.applied_at DESC""").fetchall()
    else:
        apps = conn.execute("""SELECT ia.*, u.name, u.email FROM internship_applications ia
            JOIN users u ON ia.user_id=u.id WHERE ia.user_id=? ORDER BY ia.applied_at DESC""",
                            (session['user_id'],)).fetchall()
    conn.close()
    return render_template('internships.html', apps=apps)

@app.route('/internships/apply', methods=['GET','POST'])
@login_required
def apply_internship():
    if request.method == 'POST':
        domain = request.form['domain']
        duration = request.form['duration']
        motivation = request.form['motivation']
        experience = request.form.get('experience', '')
        conn = get_db()
        conn.execute("INSERT INTO internship_applications (user_id,domain,duration,motivation,experience) VALUES (?,?,?,?,?)",
                     (session['user_id'], domain, duration, motivation, experience))
        conn.commit()
        conn.close()
        flash('Application submitted!', 'success')
        return redirect(url_for('internships'))
    return render_template('apply_internship.html')

@app.route('/internships/update/<int:aid>/<action>', methods=['POST'])
@login_required
@admin_required
def update_internship(aid, action):
    conn = get_db()
    status = 'approved' if action == 'approve' else 'rejected'
    app_row = conn.execute("SELECT * FROM internship_applications WHERE id=?", (aid,)).fetchone()
    conn.execute("UPDATE internship_applications SET status=? WHERE id=?", (status, aid))
    if status == 'approved':
        conn.execute("UPDATE users SET role='intern' WHERE id=?", (app_row['user_id'],))
        add_notification(app_row['user_id'], f'Your internship application for {app_row["domain"]} has been approved!')
    conn.commit()
    conn.close()
    flash(f'Application {status}.', 'success')
    return redirect(url_for('internships'))

# ─── DONATIONS ────────────────────────────────────────────────────────────────────

@app.route('/donations', methods=['GET','POST'])
@login_required
def donations():
    conn = get_db()
    if request.method == 'POST':
        donor = request.form['donor_name']
        email = request.form['email']
        amount = float(request.form['amount'])
        purpose = request.form.get('purpose', '')
        mode = request.form.get('payment_mode', '')
        conn.execute("INSERT INTO donations (donor_name,email,amount,purpose,payment_mode) VALUES (?,?,?,?,?)",
                     (donor, email, amount, purpose, mode))
        conn.commit()
        flash('Donation recorded! Thank you!', 'success')
    donations = conn.execute("SELECT * FROM donations ORDER BY donated_at DESC").fetchall()
    total = conn.execute("SELECT COALESCE(SUM(amount),0) FROM donations").fetchone()[0]
    conn.close()
    return render_template('donations.html', donations=donations, total=total)

@app.route('/donations/delete/<int:did>', methods=['POST'])
@login_required
@admin_required
def delete_donation(did):
    conn = get_db()
    conn.execute("DELETE FROM donations WHERE id=?", (did,))
    conn.commit()
    conn.close()
    flash('Donation record deleted.', 'danger')
    return redirect(url_for('donations'))

# ─── ANALYTICS ────────────────────────────────────────────────────────────────────

@app.route('/analytics')
@login_required
@admin_required
def analytics():
    conn = get_db()
    # Volunteer status distribution
    vol_data = conn.execute("SELECT status, COUNT(*) as cnt FROM users WHERE role='volunteer' GROUP BY status").fetchall()
    # Monthly donations
    don_data = conn.execute("""SELECT strftime('%Y-%m', donated_at) as month, SUM(amount) as total 
        FROM donations GROUP BY month ORDER BY month""").fetchall()
    # Events per month
    ev_data = conn.execute("""SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as cnt 
        FROM events GROUP BY month ORDER BY month""").fetchall()
    # Internship domains
    int_data = conn.execute("SELECT domain, COUNT(*) as cnt FROM internship_applications GROUP BY domain").fetchall()
    conn.close()

    charts = {}

    # Chart 1: Volunteer status pie
    fig, ax = plt.subplots(figsize=(5,4), facecolor='none')
    if vol_data:
        labels = [r['status'] for r in vol_data]
        sizes = [r['cnt'] for r in vol_data]
        colors_pie = ['#4CAF50','#FF9800','#F44336','#2196F3']
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors_pie[:len(labels)], startangle=90)
        ax.set_title('Volunteer Status', color='white', fontsize=13)
    ax.tick_params(colors='white')
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', transparent=True)
    buf.seek(0)
    charts['vol_status'] = base64.b64encode(buf.read()).decode()
    plt.close()

    # Chart 2: Monthly donations bar
    fig, ax = plt.subplots(figsize=(6,4), facecolor='none')
    if don_data:
        months = [r['month'] for r in don_data]
        totals = [r['total'] for r in don_data]
        ax.bar(months, totals, color='#66BB6A', edgecolor='#388E3C')
        ax.set_title('Monthly Donations (₹)', color='white', fontsize=13)
        ax.set_xlabel('Month', color='white')
        ax.set_ylabel('Amount (₹)', color='white')
        ax.tick_params(colors='white', axis='both')
        for spine in ax.spines.values(): spine.set_edgecolor('#555')
        plt.xticks(rotation=30)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', transparent=True)
    buf.seek(0)
    charts['donations'] = base64.b64encode(buf.read()).decode()
    plt.close()

    # Chart 3: Internship domains
    fig, ax = plt.subplots(figsize=(5,4), facecolor='none')
    if int_data:
        domains = [r['domain'] for r in int_data]
        cnts = [r['cnt'] for r in int_data]
        ax.barh(domains, cnts, color='#42A5F5')
        ax.set_title('Internship Domains', color='white', fontsize=13)
        ax.tick_params(colors='white', axis='both')
        for spine in ax.spines.values(): spine.set_edgecolor('#555')
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', transparent=True)
    buf.seek(0)
    charts['internships'] = base64.b64encode(buf.read()).decode()
    plt.close()

    return render_template('analytics.html', charts=charts)

# ─── CERTIFICATE ──────────────────────────────────────────────────────────────────

@app.route('/certificate/<int:uid>')
@login_required
def generate_certificate(uid):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    event_count = conn.execute("""SELECT COUNT(*) FROM event_registrations WHERE user_id=?""", (uid,)).fetchone()[0]
    conn.close()
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('dashboard'))

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=36, textColor=colors.HexColor('#1B5E20'),
                                  spaceAfter=10, alignment=TA_CENTER, fontName='Helvetica-Bold')
    sub_style = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=16, textColor=colors.HexColor('#388E3C'),
                                spaceAfter=6, alignment=TA_CENTER)
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=13, textColor=colors.HexColor('#212121'),
                                 spaceAfter=8, alignment=TA_CENTER)
    name_style = ParagraphStyle('Name', parent=styles['Normal'], fontSize=26, textColor=colors.HexColor('#1565C0'),
                                 spaceAfter=10, alignment=TA_CENTER, fontName='Helvetica-Bold')

    content = [
        Spacer(1, 0.3*inch),
        Paragraph("NayePankh Foundation", title_style),
        Paragraph("Certificate of Appreciation", sub_style),
        Spacer(1, 0.2*inch),
        Paragraph("This is to certify that", body_style),
        Paragraph(user['name'], name_style),
        Paragraph(f"has served as a valued <b>{user['role'].title()}</b> at NayePankh Foundation", body_style),
        Paragraph(f"and participated in <b>{event_count}</b> event(s) with dedication and commitment.", body_style),
        Spacer(1, 0.3*inch),
        Paragraph(f"City: {user['city'] or 'N/A'} &nbsp;&nbsp;|&nbsp;&nbsp; Skills: {user['skills'] or 'N/A'}", body_style),
        Spacer(1, 0.4*inch),
        Paragraph(f"Issued on: {datetime.now().strftime('%d %B %Y')}", body_style),
        Spacer(1, 0.3*inch),
        Paragraph("_________________________", body_style),
        Paragraph("Authorized Signatory, NayePankh Foundation", body_style),
    ]

    border_data = [[''] * 2]
    border_table = Table(border_data, colWidths=[doc.width], rowHeights=[doc.height])
    border_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 3, colors.HexColor('#1B5E20')),
        ('INNERGRID', (0,0), (-1,-1), 0, colors.white),
    ]))

    doc.build(content)
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name=f'certificate_{user["name"].replace(" ","_")}.pdf', mimetype='application/pdf')

# ─── NOTIFICATIONS ─────────────────────────────────────────────────────────────────

@app.route('/notifications/read', methods=['POST'])
@login_required
def mark_notifications_read():
    conn = get_db()
    conn.execute("UPDATE notifications SET is_read=1 WHERE user_id=?", (session['user_id'],))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/api/notifications')
@login_required
def api_notifications():
    conn = get_db()
    notifs = conn.execute("SELECT * FROM notifications WHERE user_id=? AND is_read=0 ORDER BY created_at DESC",
                          (session['user_id'],)).fetchall()
    conn.close()
    return jsonify([dict(n) for n in notifs])

@app.route('/profile', methods=['GET','POST'])
@login_required
def profile():
    conn = get_db()
    uid = session['user_id']
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        city = request.form['city']
        skills = request.form['skills']
        bio = request.form.get('bio','')
        conn.execute("UPDATE users SET name=?,phone=?,city=?,skills=?,bio=? WHERE id=?",
                     (name, phone, city, skills, bio, uid))
        conn.commit()
        session['name'] = name
        flash('Profile updated!', 'success')
    user = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    my_events = conn.execute("""SELECT e.* FROM events e 
        JOIN event_registrations r ON e.id=r.event_id WHERE r.user_id=?""", (uid,)).fetchall()
    conn.close()
    return render_template('profile.html', user=user, my_events=my_events)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
