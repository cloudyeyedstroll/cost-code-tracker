# Construction Job Costing MVP

## Project Overview
A mobile-first, production-ready Construction Job Costing application designed to allow field foremen to log labor, equipment, materials, and subcontractor hours securely on their mobile devices, and for the office to view and export aggregated daily summaries. The application uses Python and Streamlit for the frontend/backend and is fully containerized and live on Google Cloud Run at: [https://cost-code-tracker-94816924591.us-central1.run.app/](https://cost-code-tracker-94816924591.us-central1.run.app/). It leverages a live Supabase (PostgreSQL) production cluster for scalable, highly-available cloud data persistence.

## What Has Been Done

### 1. Database Architecture (Supabase / PostgreSQL)
- **Cloud Database Migration:** Transitioned from a local development database to a live Supabase PostgreSQL production cluster.
- Built a robust, cloud-native schema mapped via Supabase with tables for `projects`, `employees`, `equipment`, `cost_codes`, `labor_logs`, `equipment_logs`, and `force_accounts`.
- **Advanced Tracking Schemas:** Deployed robust table updates for `report_photos`, `material_logs` (tracking supplier, quantities, and import/export spoils), and `subcontractor_logs` (tracking company name, scope of work, hours, and ticket uploads).
- **Force Account Architecture:** Added a dedicated schema structure for grouping T&M logs to signed tickets.
- **Project-Specific Scoping Engine:** Restructured Cost Codes and Equipment from global generic lists to project-specific mappings using a Many-to-Many relational database model (`project_cost_codes` and `project_equipment`).

### 2. Security & User Flow
- **Supabase Auth:** Integrated secure, email/password-based authentication with onboarding activation links. 
- **Automated Email Invitations & Password Resets:** Implemented Supabase's native GoTrue Auth system for sending branded cloud-managed emails securely. Solves Streamlit URL hash limitations via a secure `token_hash` query parameter intercept block that seamlessly authenticates and activates users.
- **Bulletproof Environment Configuration:** Upgraded the configuration loader to bypass Streamlit caching issues, ensuring production credentials initialize flawlessly. Included dynamic fallback logic and secret sanitization to protect against malformed variables.
- **Session State Management:** Maintained active login states using Streamlit's session state, tying logs strictly to the authenticated user profile.
- **Dynamic Job Titles & Roles:** Configurable roles via `job_titles` map securely to system permission tiers (Admin, Foreman, Crew).

### 3. Mobile-First Field Logging
- **Dynamic Shift Allocation:** Field workers now log explicit Shift Start and End Times. The app auto-calculates total shift duration and strictly enforces a multi-step allocation UI.
- **Unlimited & Scalable Cost Code Allocation:** Dynamic form structure allows adding unlimited cost code allocations, backed by strict mathematical validations.
- **Material & Subcontractor Tracking:** Fully built-out mobile interfaces for logging materials (e.g. soil import/export) and hired subcontractor services, complete with the ability to upload physical tickets directly to Supabase storage.
- **Automated Equipment Mirroring & SMU Tracking:** A conditional heavy equipment workflow auto-clones labor hours into equipment logs, tracks start/end hour meters (SMU), and calculates exact runtimes.
- **Historical Form Persistence:** "Sticky" defaults automatically remember and pre-populate the active Project, Cost Code, and Equipment inputs based on recent submissions.

### 4. Office Dashboard & Reporting
- **Live Cost Tracking:** Integrated financial calculations directly into SQL queries to present real-time "Total Labor Cost ($)" and "Total Equipment Cost ($)" on the dashboard.
- **Automated Daily Blueprint PDF Reporting:** Deployed a new Reporting Engine (`reporting.py`) utilizing `fpdf2`. This generates a high-fidelity, multi-page executive PDF document combining crew resources, fleet utilization, materials, subcontractors, and production logs. Features an automatic, mathematically centered company branding ingestion system.
- **AI-Powered OCR Architecture Prepared:** Began scaffolding for the `ai_vision.py` pipeline to ingest subcontractor/material tickets, send them through an LLM vision API, and automatically parse key fields (ticket number, company name, scope, hours).
- **Consolidated Admin Management:** Consolidated project deployment, cost code ingestion, and fleet management into unified structured administrative containers.
- **Force Account Sign-off (T&M):** Deployed a dedicated view for Foremen/Admins to generate Time & Material tickets (Cost Code 99-000), complete with digital signature capture via `streamlit-drawable-canvas`.
- **Data Export:** Integrated one-click CSV export functionality for all major log tables to streamline billing workflows.

---

## Planned Features & Next Steps

### 1. High Priority 1: AI Vision OCR Pipeline for Ticket Parsing
- **Goal:** Fully activate the AI Vision OCR pipeline (`ai_vision.py`) integrated directly into the subcontractor and material logging forms. 
- **Why:** To completely eliminate manual data entry for foremen. When a ticket photo is uploaded, the AI will automatically extract properties like Ticket Number, Company Name, Scope of Work, and Hours, returning strict JSON payloads to instantly populate the database.

### 2. High Priority 2: PWA Service Worker & Manifest Deployment
- **Goal:** Deploy a `manifest.json` and a Service Worker to transform the Streamlit application into a Progressive Web App (PWA).
- **Why:** To allow users to "Add to Homescreen" for a native, app-like mobile experience without downloading from the App Store, and to pave the way for offline data caching when cellular service drops on remote jobsites.

### 3. High Priority 3: Procore/Accounting API Bidirectional Sync
- **Goal:** Connect to the Procore API and leading accounting suites.
- **Why:** To enable automated, bidirectional syncing of Projects, Cost Codes, Employees, and Equipment. The database schema has already been prepped with `procore_id` columns to support this enterprise-grade synchronization.
