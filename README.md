# CCS Internship Management System

Flask + MySQL skeleton built from your wireframes. Pure Python on the
backend (Flask, SQLAlchemy, Flask-Login) — the only JavaScript in the
project is vanilla JS for UI interactivity (password show/hide, role
card selection, drag-and-drop uploads, tabs). No JS framework, no build
step.

## What's included

| Wireframe screen | Route | Template |
|---|---|---|
| Landing + Login | `/` | `templates/landing.html` |
| Create Account | `/auth/register` | `templates/auth/register.html` |
| Student Profile | `/student/profile` | `templates/student/profile.html` |
| Student Dashboard | `/student/dashboard` | `templates/student/dashboard.html` |
| Report Submission | `/student/reports` | `templates/student/reports.html` |
| Certificate | `/student/certificate` | `templates/student/certificate.html` |
| Admin Dashboard | `/admin/dashboard` | `templates/admin/dashboard.html` |
| Partner Dashboard (stub) | `/partner/dashboard` | `templates/partner/dashboard.html` |

Working now:
- Registration (student / industry partner roles) writing to MySQL
- Login / logout with hashed passwords (Flask-Login sessions)
- Role-based access control (`@role_required`) so students can't open
  admin routes and vice versa
- Weekly + narrative report file uploads, saved under `uploads/` and
  recorded in the database
- Skill chips on the student profile
- All dashboards read real data from the database (empty states are
  handled — e.g. "No active internship yet" before a placement exists)

Marked as **TODO / next steps** (routes exist as placeholders in the
sidebar but aren't wired up yet):
- Internship Application, Hours Tracking, Evaluation forms
- Admin CRUD for students / companies / announcements
- Certificate PDF generation (the page renders a preview; "Download
  PDF" currently has no backend behind it)
- Partner-side evaluation submission

## 1. Set up MySQL

```sql
CREATE DATABASE ims_db CHARACTER SET utf8mb4;
```

## 2. Configure environment

```bash
cd ims_app
cp .env.example .env
# edit .env and set DB_USER / DB_PASSWORD / DB_NAME to match your MySQL setup
```

## 3. Install dependencies

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 4. Create tables + demo data

```bash
python seed.py
```

This creates every table and inserts one demo account per role so you
can see all the pages populated immediately:

| Role | Email | Password |
|---|---|---|
| Student | juan.delacruz@email.com | password123 |
| Admin | admin@ccs.edu | password123 |
| Industry Partner | partner@techsolutions.com | password123 |

## 5. Run the app

```bash
python app.py
```

Visit `http://127.0.0.1:5000`.

## Project structure

```
ims_app/
├── app.py                 # application factory
├── config.py               # env-driven config (MySQL URI, uploads, etc.)
├── extensions.py            # db, login_manager, migrate instances
├── models.py                # all SQLAlchemy models
├── decorators.py            # @role_required access control
├── seed.py                  # creates tables + demo data
├── routes/
│   ├── main.py               # landing page, dashboard redirect
│   ├── auth.py                # login / register / logout
│   ├── student.py              # dashboard, profile, reports, certificate
│   ├── admin.py                # admin dashboard
│   └── partner.py              # partner dashboard (stub)
├── templates/                # Jinja2 templates, one per wireframe screen
├── static/css/style.css        # navy/gold theme matching the wireframes
├── static/js/main.js            # vanilla JS for interactive UI only
└── uploads/                   # uploaded report/document files (gitignored)
```

## Suggested next steps for your capstone write-up

1. Wire up the **Internship Application** flow (student applies to a
   partner company; admin/adviser approves and creates the `Internship` row).
2. Build the **Hours Tracking** page — right now `completed_hours` only
   updates through the seed script; you'll want a form (student self-report
   or supervisor-approved) that updates it.
2. Add **Evaluation** forms for supervisors/advisers to score interns —
   the `Evaluation` model is ready, there's just no form yet.
3. Generate the certificate as an actual PDF (the `pdf` skill / a library
   like `reportlab` or `weasyprint` works well here) once all completion
   flags on `Certificate` are true.
4. Build out the Admin CRUD screens (Students, Partner Companies,
   Announcements, Settings) — currently placeholders in the sidebar.
