# WASTECLEAN – AI-Driven Digital Waste Management & Collection Optimization Platform

## Upgraded Capstone Progress Demo

This version is designed specifically for the SRS / Progress Evaluation demo. The application now gives **four different role-specific workspaces** instead of showing the same dashboard to every user.

### What changed in this version

- Professional product-style landing/login page
- Quick demo login buttons for all four roles
- Distinct **Citizen Workspace**
- Distinct **Supervisor Control Room**
- Distinct **Collector Field Workspace**
- Distinct **Admin Console**
- Role-based navigation and access control
- Citizen reporting and personal report tracking
- Supervisor AI-prioritized dispatch queue
- Collector task execution with Assigned → In Progress → Completed workflow
- Admin user/role directory, platform KPIs and demo-data reset
- AI priority, confidence and reason shown in operational workflows
- GIS map for waste reports and collection locations
- Analytics for priority distribution, waste categories and recurring hotspots
- Seeded demo assignments so the Collector dashboard is populated immediately

## Demo credentials

| Role | Email | Password | Main demo purpose |
|---|---|---|---|
| Citizen | citizen@wasteclean.demo | demo123 | Report and track waste |
| Supervisor | supervisor@wasteclean.demo | demo123 | Review, prioritize and assign |
| Collector | collector@wasteclean.demo | demo123 | Execute and close tasks |
| Admin | admin@wasteclean.demo | demo123 | Monitor and control platform |

Additional collector: `neha.collector@wasteclean.demo / demo123` (display name: Collector User 2)

## Recommended mentor demonstration

### 1. Start with the login page
Show the product-style front page and explain the four user roles. Click **Supervisor** or **Citizen** quick access to demonstrate the role-based entry.

### 2. Citizen workflow
Login as Citizen → **Report Waste** → select waste type → enter:

> Overflowing garbage pile near market with foul smell

Choose a map location → submit → show the AI-generated priority and confidence → return to Citizen Dashboard and show the report status.

### 3. Supervisor workflow
Logout → login as Supervisor → show the **AI-Prioritized Dispatch Queue** → inspect priority, confidence and reason → select a Collector + deadline → **Dispatch**.

### 4. Collector workflow
Logout → login as Collector → show **My Field Tasks** → open the assigned case → change **Assigned → In Progress → Completed**.

### 5. Admin workflow
Logout → login as Admin → show **System Administration** → user/role directory → platform KPIs → all reports/tasks → Analytics → optionally restore demo data.

### 6. Close with the system story

**Citizen Report → AI Analysis → Priority → Supervisor Dispatch → Collector Execution → Status Update → KPI / Analytics**

That flow directly demonstrates the software-engineering contribution of the project.

## Technology

- Python + Flask
- SQLite
- scikit-learn TF-IDF + Logistic Regression proof-of-concept AI classifier
- HTML5 / CSS3 / JavaScript
- Leaflet + OpenStreetMap for GIS visualization
- Role-based session access control

## Run on Windows

1. Install Python 3.10+ and ensure `py` works from Command Prompt.
2. Extract the ZIP.
3. Double-click `run.bat`.
4. The launcher creates `.venv`, installs `requirements.txt`, and starts the application.
5. Open `http://127.0.0.1:5000`.

Or manually:

```bash
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

## Important prototype note

The AI component is intentionally local and reproducible. It uses a small embedded demonstration dataset and scikit-learn, so the mentor demo does not depend on Gemini/OpenAI API quotas. For a production system, the model would need a representative municipal waste dataset, proper validation, secure password hashing, stronger authorization, audit logging, privacy controls and production deployment.

The current image-upload control in the reporting screen is kept as a UI placeholder; the demo's implemented AI classification is text/operational-context based. This should be presented honestly during evaluation.

## Originality / copyright

The application code and project-specific workflow in this package were created for this capstone demo. Third-party libraries remain under their respective licenses. The project should be described as an original student implementation/integration rather than a claim that the underlying waste-management problem has never been addressed anywhere.
