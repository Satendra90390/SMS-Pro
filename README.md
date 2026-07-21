# SMS Pro — Student Management System

> A full-featured, multi-tenant student management platform for educational institutions.

**Live Demo:** [sms-pro.onrender.com](https://sms-pro.onrender.com/)

---

## Overview

SMS Pro is a role-based web application built with Django that helps schools, colleges, universities, and coaching centers manage students, faculty, courses, attendance, grades, and fees — all from a single dashboard.

It includes **STAN**, an AI assistant powered by Groq's Llama 3.1, context-aware to your institution's data.

## Features

### Role-Based Dashboards
- **Admin** — Full control: manage students, faculty, subjects, fees, reports, and analytics
- **Faculty** — View teaching assignments, department info
- **Student** — View results, fees, and quick actions
- **Parent** — Monitor child's grades and attendance

### Core Functionality
- **Student Management** — Add, search, and delete students with account credentials
- **Faculty Management** — Register faculty with department, qualification, and login access
- **Course & Subject Management** — Create courses, assign faculty to teach specific subjects
- **Attendance Tracking** — Record daily present/absent/late status per student
- **Results & Grades** — Track student performance across courses with letter grades
- **Fee Management** — Track tuition, exam, and other fees with Paid/Pending/Partial status
- **System Analytics** — Student-faculty ratio, attendance rate, and summary stats with charts

### AI Assistant (STAN)
- Context-aware chatbot that knows your institution's data
- Ask about students, attendance, fees, or get summaries
- Powered by Groq Llama 3.1 8B

### Design
- **Dual Theme** — Light mode (professional, soft gradients) and dark mode (glassmorphism, neon glow)
- **Responsive** — Works on desktop, tablet, and mobile with hamburger menu
- **Lucide Icons** — Crisp vector icons throughout the interface
- **Chart.js** — Doughnut charts for analytics visualizations

### Authentication
- Custom user model with role-based access (Admin / Faculty / Student / Parent)
- OAuth login via Google and GitHub (django-allauth)
- Institution registration with 2-step wizard (details + admin account)
- Password strength indicator

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 6.0.7, Python 3.12 |
| Database | PostgreSQL 16 (SQLite for dev) |
| Auth | django-allauth 65.x (OAuth + credentials) |
| AI Chat | Groq API (Llama 3.1 8B) |
| Frontend | Custom CSS (dual-theme design system), Lucide Icons, Chart.js |
| Deployment | Render.com, Docker |
| Static Files | Whitenoise |

## Project Structure

```
sms-django/
├── sms_django/           # Project config (settings, urls, wsgi)
├── accounts/             # Auth, user model, OAuth, landing page
├── core/                 # Business logic, models, dashboards, AI chat
├── templates/            # HTML templates
│   ├── components/       # Reusable sidebar templates
│   ├── admin_panel/      # Admin dashboard pages
│   ├── faculty/          # Faculty dashboard
│   ├── student/          # Student dashboard
│   ├── parent/           # Parent dashboard
│   └── accounts/         # Login, register, landing, role-select
├── static/css/           # theme.css, style.css, auth.css, chat.css, landing.css
├── Dockerfile
├── docker-compose.yml
└── render.yaml
```

## Getting Started

### Prerequisites
- Python 3.12+
- PostgreSQL (or use SQLite for development)
- A Groq API key (for STAN chatbot)

### Local Development

```bash
# Clone the repository
git clone https://github.com/Satendra90390/SMS-Pro.git
cd SMS-Pro

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your values

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Seed demo data (optional)
python seed.py

# Start development server
python manage.py runserver
```

### Environment Variables

```env
DJANGO_SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Optional — OAuth
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=

# Optional — AI Chatbot
GROQ_API_KEY=
```

### Docker Deployment

```bash
docker compose up -d --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

### Render.com Deployment

The project includes `render.yaml` for automatic deployment. Just connect your GitHub repo to Render and it will configure the web service and PostgreSQL database automatically.

## Demo Credentials

After running `python seed.py`, use these to log in:

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Faculty | faculty1 | pass1234 |
| Student | student1 | pass1234 |
| Parent | parent1 | pass1234 |

## License

This project is open source and available under the [MIT License](LICENSE).
