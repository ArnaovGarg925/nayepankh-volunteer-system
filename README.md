# 🌿 NayePankh AI Volunteer Management System

A modern, full-featured NGO Management System built with Python Flask for managing volunteers, interns, events, donations, and more.

![Python](https://img.shields.io/badge/Python-3.8+-blue) ![Flask](https://img.shields.io/badge/Flask-3.0-green) ![SQLite](https://img.shields.io/badge/Database-SQLite-orange) ![Bootstrap](https://img.shields.io/badge/UI-Bootstrap5-purple)

---

## 🚀 Features

- 🔐 User Registration / Login / Logout
- 👥 Role-based Access — Admin, Volunteer, Intern
- ✅ Volunteer Management (Add / Edit / Delete / Approve / Search)
- 📋 Internship Applications (Apply / Approve / Reject)
- 📅 Event Management (Create / Register / View / Delete)
- 💰 Donation Management & Tracking
- 📊 Admin Dashboard with Statistics
- 📈 Analytics Dashboard with Charts (Matplotlib)
- 🏆 PDF Certificate Generator (ReportLab)
- 🌙 Dark / Light Mode Toggle
- 🔔 Real-time Notifications
- 📱 Fully Responsive UI (Bootstrap 5)
- 🔍 Search & Filter functionality

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python Flask |
| Database | SQLite |
| Frontend | HTML, CSS, JavaScript |
| UI Framework | Bootstrap 5 |
| Charts | Matplotlib |
| Data | Pandas |
| PDF | ReportLab |

---

## ⚙️ Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/nayepankh-volunteer-system.git
cd nayepankh-volunteer-system
```

### 2. Create virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the app
```bash
python app.py
```

### 5. Open in browser
http://127.0.0.1:5000

---

## 🔑 Default Login Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@nayepankh.org | admin123 |
| Volunteer | Register yourself | Pending approval |

---

## 📁 Project Structure
nayepankh/

├── app.py                  # Main Flask application

├── requirements.txt        # Python dependencies

├── static/

│   ├── style.css           # Custom stylesheet (dark/light theme)

│   └── script.js           # JavaScript (animations, notifications)

└── templates/

├── base.html           # Base layout with navbar

├── index.html          # Landing page

├── login.html          # Login page

├── register.html       # Registration page

├── dashboard.html      # Admin & user dashboard

├── volunteers.html     # Volunteer management

├── events.html         # Event listings

├── internships.html    # Internship applications

├── donations.html      # Donation management

├── analytics.html      # Charts & analytics

└── profile.html        # User profile

---

## 📸 Screenshots

> Add screenshots of your project here after running it locally.

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first.

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

## 👨‍💻 Developer

Made with ❤️ for **NayePankh Foundation**  
Empowering communities through volunteerism across India.
