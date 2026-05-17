# Construction Job Costing MVP

A mobile-first, production-ready application designed to streamline field labor and equipment tracking for construction teams. This tool empowers foremen and field workers to securely log their hours on mobile devices while providing the back-office with real-time financial tracking and actionable data exports.

## 🚀 Key Features

### 📱 Mobile-First Field Logging
- **Shift-Based Time Cards:** Workers log precise Shift Start and End Times with optional lunch deductions. The system auto-calculates total shift duration.
- **Validated Cost Allocation:** Shift hours can be split across an unlimited number of independent cost codes using a dynamic allocation flow. Strict server-side validation ensures that the sum of allocated hours exactly matches the total shift duration, preventing bad data from entering payroll.
- **Equipment Tracking:** Log exact machinery (Make, Model, and Unit Number) to accurately track asset utilization alongside labor.
- **Optimized UI:** High-contrast, large-touch-target interface tailored for outdoor visibility and ease of use on mobile devices.

### 🛡️ Foreman Approval Workflow
- **Role-Based Access Control:** Differentiates between standard crew members and foremen.
- **Field Oversight:** Foremen get an exclusive "Foreman Review" view to audit and bulk-approve pending labor and equipment logs before they hit the office.

### 💼 Office Dashboard & Live Costing
- **Real-Time Financials:** Live calculation of "Total Labor Cost ($)" and "Total Equipment Cost ($)" based on underlying hourly wage and machine charge-out rates.
- **Automated Aggregation:** Daily summaries automatically group hours by cost code and equipment assets.
- **Force Account & T&M Tickets:** Dedicated interface for generating and reviewing Time & Material tickets (Cost Code 99-000) equipped with digital signature captures rendering securely on the dashboard.
- **One-Click Exports:** Export labor and equipment reports directly to CSV to streamline invoicing, payroll, and bidding workflows.

### 🔒 Security & Data Integrity
- **Secure Authentication:** Robust integration with Supabase Auth using email, passwords, and secure activation links.
- **Automated Invites:** Integrated Supabase's native GoTrue Admin Auth system. Automatically fires cloud-managed activation emails, utilizing a secure URL `token_hash` intercept pattern to initialize sessions and capture passwords natively within Streamlit.
- **Dynamic Job Titles:** Create and manage custom job titles that map securely to system permission tiers (Admin, Foreman, Crew).
- **Session Management:** Prevents data entry mix-ups by strictly tying logged hours to the currently authenticated user profile.
- **Supabase Database:** Hosted PostgreSQL ensuring fully relational, highly-available cloud data persistence.

## 🛠️ Technology Stack
- **Frontend/Backend:** [Python](https://www.python.org/) & [Streamlit](https://streamlit.io/)
- **Digital Signatures:** `streamlit-drawable-canvas`
- **Database & Auth:** [Supabase](https://supabase.com/) (PostgreSQL)
- **Data Manipulation:** Pandas
- **Environment Management:** `python-dotenv` (robust parsing across CLI entrypoints)
- **Cloud Infrastructure:** Google Cloud Run (Containerized Deployment)

## 🔮 Future Roadmap
- **Procore API Integration:** Bidirectional syncing of Projects, Cost Codes, and Employees directly with Procore.
- **Advanced Analytics:** Adding date range pickers and preset filters to the Office Dashboard.

## 🏃‍♂️ Getting Started

### Prerequisites
Make sure you have Python installed, then install the required dependencies:
```bash
pip install streamlit pandas
```

### Running the Application
Navigate to the project directory and launch the Streamlit server:
```bash
streamlit run app.py
```
The application will be available at `http://localhost:8501`.
