# Construction Job Costing MVP

## Project Overview
A mobile-first, production-ready Construction Job Costing application designed to allow field foremen to log labor and equipment hours securely on their mobile devices, and for the office to view and export aggregated daily summaries. The application uses Python and Streamlit for the frontend/backend and Supabase (PostgreSQL) for scalable cloud data persistence.

## What Has Been Done

### 1. Database Architecture (Supabase / PostgreSQL)
- Built a robust, cloud-native schema mapped via Supabase with `projects`, `employees`, `equipment`, `cost_codes`, `labor_logs`, `equipment_logs`, and `force_accounts` tables.
- Implemented robust DB initialization and data seeding with realistic civil construction infrastructure scenarios.
- Added `hourly_rate` to calculate live costs, `is_foreman` for role-based access, and a `status` field for the approval workflow.
- Included `start_time` and `end_time` to labor logs to capture explicit shift durations.
- Prepared schema for future integrations by including `procore_id` fields in relevant tables.
- **Force Account Architecture:** Added a dedicated schema structure for grouping T&M logs to signed tickets, executing schema migration `20260517000000_force_accounts.sql`.
- **Dynamic Job Titles:** Replaced hardcoded roles with a dynamic, database-driven `job_titles` table mapped to core permission tiers (Admin, Foreman, Crew). Admins can create and assign custom job titles through the Office Dashboard.

### 2. Security & User Flow
- **Supabase Auth:** Integrated secure, email/password-based authentication with onboarding activation links. Added secure Invite Token logic for standardizing new employee rollouts.
- **Automated Email Invitations:** Implemented Supabase's native GoTrue Admin Auth invite system. Triggers branded cloud-managed emails securely via the `supabase_admin` client. Solves Streamlit URL hash limitations via a secure `token_hash` query parameter intercept block that seamlessly authenticates and activates new users.
- **Bulletproof Environment Configuration:** Upgraded the configuration loader with `dotenv_values` and `find_dotenv()` to bypass Streamlit working directory caching issues, ensuring production credentials and database connections initialize flawlessly across all environments.
- **Session State Management:** Maintained active login states using Streamlit's session state, ensuring workers can only log hours under their authenticated profile to prevent data entry errors.
- **Role-Based Navigation:** The application dynamically adjusts navigation, granting foremen an exclusive "Foreman Review" view to bulk-approve pending logs.
- **Admin Management:** Introduced strict administrative controls for permanently deleting employee records (with log conflict validation) and updating roles.
- **Cloud Config Fallbacks:** Implemented robust configuration parsing in `database.py` to seamlessly fallback to `st.secrets` when cloud environment variables are unavailable, preventing deployment crashes.

### 3. Mobile-First Field Logging
- **Dynamic Shift Allocation:** Field workers now log explicit Shift Start and End Times. The app auto-calculates total shift duration and strictly enforces a multi-step allocation UI. We replaced the fixed 3-slot limit with a dynamic form structure that allows adding unlimited cost code allocations using a responsive "➕ Add Another Cost Code" button, and the ability to selectively delete allocations via a "🗑️ Remove" button.
- **Validation Gates:** Forms are protected by strict validations, showing clear errors and blocking submission if allocated hours do not match the calculated shift duration.
- **Responsive Layout:** Changed the Streamlit layout to "centered" to prevent horizontal stretching on small screens.
- **Improved Navigation:** Replaced horizontal tabs with a `st.selectbox` for toggling between views.
- **Enhanced Touch Targets:** Injected custom CSS to enlarge fonts to 18px and force submission buttons to full-width, 3.2em height with distinct colors for outdoor visibility and ease of use.
- **Comprehensive Logging:** Added functionality to log both labor (with an optional text-based work description) and equipment hours.

### 4. Office Dashboard & Reporting
- **Live Cost Tracking:** Integrated financial calculations directly into SQL queries to present real-time "Total Labor Cost ($)" and "Total Equipment Cost ($)" on the dashboard.
- **Data Summaries:** Created SQL queries to aggregate daily labor and equipment hours.
- **Asset Tracking:** Refined equipment summary queries to track and display specific machinery (Unit Number & Make/Model) alongside aggregate cost code hours.
- **Data Export:** Integrated one-click CSV export functionality for both labor and equipment reports to streamline billing workflows.
- **Project & Job Management:** Added an intuitive, dynamic project creation interface allowing administrators to instantly spin up and deploy new jobs to field crews directly from the Office Dashboard without backend migrations.
- **Force Account Sign-off (T&M):** Deployed a dedicated view for Foremen/Admins to generate Time & Material tickets (Cost Code 99-000), complete with digital signature capture via `streamlit-drawable-canvas`. Signed tickets render seamlessly on the Office Dashboard.

---

## Planned Features & Next Steps

### 1. Procore Integration
- **Goal:** Connect to the Procore API.
- **Why:** To enable automated, bidirectional syncing of Projects, Cost Codes, Employees, and Equipment. The database schema has already been prepped with `procore_id` columns to support this.

### 3. Advanced Dashboard Filtering
- **Goal:** Implement date range pickers and preset filters (e.g., "Last 7 Days", "Last 30 Days", "Current Month").
- **Why:** To improve performance and usability on the Office Dashboard as the dataset grows over time.

### 4. Production Deployment
- **Goal:** Deploy the application to Firebase (using Firebase Hosting combined with Cloud Run for the Python backend).
- **Why:** To distribute the application to the field crew via a standard URL using Google's scalable Firebase platform. This relies heavily on completing the Cloud Database Migration first.

### 5. Unlimited & Scalable Cost Code Allocation (10+ Codes)
- **Goal:** Expand the frontend time card interface from a fixed 3-slot allocation loop to a dynamic, unlimited row-generation system.
- **Why:** To support complex, multi-activity field shifts where crew members or heavy equipment operators bounce between 10 or more distinct tasks during a single shift, ensuring the strict duration validation gates remain active no matter how many codes are added.
