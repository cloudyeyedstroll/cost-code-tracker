# Construction Job Costing MVP

A mobile-first, production-ready application designed to streamline field labor and equipment tracking for construction teams. This tool empowers foremen and field workers to securely log their hours, materials, and subcontractor tickets on mobile devices while providing the back-office with real-time financial tracking and actionable data exports. 

The application is fully containerized and live on **Google Cloud Run** at: [https://cost-code-tracker-94816924591.us-central1.run.app/](https://cost-code-tracker-94816924591.us-central1.run.app/). It utilizes a live **Supabase PostgreSQL** production cluster for highly-available cloud data persistence.

## 🚀 Key Features

### 1. Mobile-First Field Logging
- **Shift-Based Time Cards:** Workers log precise Shift Start and End Times with optional lunch deductions. The system auto-calculates total shift duration.
- **Unlimited Validated Cost Allocation:** Shift hours can be split across an unlimited number of independent cost codes using a dynamic allocation flow. Strict server-side validation ensures that the sum of allocated hours exactly matches the total shift duration, preventing bad data from entering payroll.
- **Project-Specific Scoping Engine:** Time cards automatically isolate Cost Codes and Equipment fleets down to the exact assets mapped to the selected project via relational junction tables, removing unneeded global clutter for field crews.
- **Automated Equipment Mirroring & SMU Tracking:** A conditional 'Heavy Equipment' checkbox workflow auto-clones labor hours into equipment logs. It tracks start/end hour meters (SMU) and calculates exact runtimes.
- **Material & Subcontractor Tracking:** Dedicated tabs for logging materials (including import/export spoils) and subcontractor/hired services with scope of work, hours, and ticket attachments.

### 2. Foreman Approval Workflow & Force Account Sign-off
- **Role-Based Access Control:** Differentiates between standard crew members, foremen, and admins.
- **Field Oversight:** Foremen get an exclusive "Foreman Review" view to audit and bulk-approve pending labor and equipment logs before they hit the office.
- **Force Account & T&M Tickets:** Dedicated interface for generating and reviewing Time & Material tickets equipped with digital signature captures rendered securely on the dashboard.

### 3. Office Dashboard & Live Costing
- **Real-Time Financials:** Live calculation of "Total Labor Cost ($)" and "Total Equipment Cost ($)" based on underlying hourly wage and machine charge-out rates.
- **Consolidated Admin Management:** A unified workspace controls project initialization, manual cost code generation, and bulk CSV spreadsheet imports.
- **Automated Daily Blueprint PDF Reporting:** One-click generation of high-fidelity, multi-page executive PDF reports containing crew manpower, fleet utilization, materials, and production notes. Supports custom company branding with automatic center-aligned logo ingestion directly from the dashboard.
- **One-Click Exports:** Export labor, equipment, materials, and subcontractor logs directly to CSV to streamline invoicing, payroll, and bidding workflows.

### 4. Security & Data Integrity
- **Secure Authentication:** Robust integration with Supabase Auth using email, passwords, and secure activation/reset links (with token intercept workflows).
- **Session Management:** Prevents data entry mix-ups by strictly tying logged hours to the currently authenticated user profile.
- **Database Schema Upgrades:** Enhanced tables for `report_photos`, `material_logs`, and `subcontractor_logs` featuring robust relational linkages to projects and cost codes.

## 🛠️ Technology Stack
- **Frontend/Backend:** [Python](https://www.python.org/) & [Streamlit](https://streamlit.io/)
- **Digital Signatures:** `streamlit-drawable-canvas`
- **Database & Auth:** [Supabase](https://supabase.com/) (PostgreSQL)
- **Data Manipulation:** Pandas
- **PDF Generation:** `fpdf2`
- **Cloud Infrastructure:** Google Cloud Run (Containerized Deployment)

## 🔮 Future Roadmap (Next Steps)
1. **High Priority 1: AI Vision OCR Pipeline for Ticket Parsing:** Implement AI-powered vision parsing so uploaded material and subcontractor tickets are automatically scanned and their data extracted into the log fields.
2. **High Priority 2: PWA Service Worker & Manifest Deployment:** Transform the application into a Progressive Web App (PWA) to allow offline caching, home-screen installation, and a native mobile feel.
3. **High Priority 3: Procore/Accounting API Bidirectional Sync:** Connect to the Procore API and accounting software to enable automated, bidirectional syncing of Projects, Cost Codes, Employees, and Equipment.

## 🏃‍♂️ Getting Started

### Prerequisites
Make sure you have Python installed, then install the required dependencies:
```bash
pip install -r requirements.txt
```

### Running the Application
Navigate to the project directory and launch the Streamlit server:
```bash
streamlit run app.py
```
The application will be available at `http://localhost:8501`.
