import streamlit as st
import datetime
import database as db
import secrets

st.set_page_config(page_title="Construction Job Costing", layout="centered")

st.markdown("""
<style>
/* Custom CSS for mobile-first UI */
.block-container {
    padding-top: 1.5rem !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
}
div[data-testid="stFormSubmitButton"] > button {
    width: 100% !important;
    height: 3.2em !important;
    font-weight: bold !important;
    background-color: #FF4B4B !important;
    color: white !important;
    border-radius: 8px !important;
    border: none !important;
}
div[data-testid="stFormSubmitButton"] > button:hover {
    background-color: #ff3333 !important;
    color: white !important;
}
p, label, div[data-baseweb="select"] *, div[data-baseweb="radio"] * {
    font-size: 18px !important;
}
</style>
""", unsafe_allow_html=True)

# Initialize database
db.setup()

# Check for invitation link
if "invite" in st.query_params:
    token = st.query_params["invite"]
    pending_emp = db.get_employee_by_token(token)
    
    if not pending_emp or pending_emp['account_status'] != 'Pending':
        st.query_params.clear()
        st.error("Invalid or expired invitation link.")
        if st.button("Return to Login"):
            st.rerun()
        st.stop()
        
    st.header("Activate Your Account")
    st.write(f"Welcome {pending_emp['first_name']}! Please set up a password to activate your time card account.")
    
    with st.form("activation_form"):
        new_password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submit_activation = st.form_submit_button("ACTIVATE ACCOUNT", use_container_width=True)
        
        if submit_activation:
            if not new_password or not confirm_password:
                st.error("Please fill in all fields.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            elif len(new_password) < 6:
                st.error("Password must be at least 6 characters long.")
            else:
                db.activate_employee_account(pending_emp['id'], new_password)
                st.query_params.clear()
                st.success("Account activated successfully! You can now log in.")
                import time; time.sleep(1.5)
                st.rerun()
    st.stop()

if 'logged_in_user_id' not in st.session_state:
    st.session_state.logged_in_user_id = None
if 'logged_in_user_name' not in st.session_state:
    st.session_state.logged_in_user_name = None
if 'logged_in_user_role' not in st.session_state:
    st.session_state.logged_in_user_role = None

st.title("Construction Job Costing")

if st.session_state.logged_in_user_id is None:
    st.header("Employee Login")
    
    with st.form("login_form"):
        email = st.text_input("Email Address")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("LOG IN", use_container_width=True)
        
        if submit:
            emp_data = db.verify_employee_login(email, password)
            if emp_data:
                st.session_state.logged_in_user_id = emp_data["id"]
                st.session_state.logged_in_user_name = emp_data["full_name"]
                st.session_state.logged_in_user_role = emp_data["role"]
                st.rerun()
            else:
                st.error("Incorrect Email or Password. Please try again.")

else:
    st.success(f"Logged in as: {st.session_state.logged_in_user_name}")
    if st.button("Log Out"):
        st.session_state.logged_in_user_id = None
        st.session_state.logged_in_user_name = None
        st.session_state.logged_in_user_role = None
        st.rerun()

    role = st.session_state.logged_in_user_role
    if role == 'Crew':
        view = "Field Logging"
    elif role == 'Foreman':
        view = st.selectbox("Select View", ["Field Logging", "Foreman Review"])
    elif role == 'Admin':
        view = st.selectbox("Select View", ["Field Logging", "Foreman Review", "Office Dashboard"])

    if view == "Field Logging":
        st.header("Log Field Hours")
        
        log_type = st.radio("Log Type", ["Labor", "Equipment"], horizontal=True)
        
        projects_df = db.get_projects()
        cost_codes_df = db.get_cost_codes()
        
        with st.form("log_form", clear_on_submit=True):
            log_date = st.date_input("Date", datetime.date.today())
            
            project_options = dict(zip(projects_df['project_name'], projects_df['id']))
            selected_project = st.selectbox("Project", list(project_options.keys()))
            
            cost_code_options = dict(zip(cost_codes_df['display_name'], cost_codes_df['id']))
            
            if log_type == "Labor":
                st.subheader("Step 1: Shift Time Entry")
                col1, col2 = st.columns(2)
                with col1:
                    start_time = st.time_input("Shift Start Time", datetime.time(7, 0))
                with col2:
                    end_time = st.time_input("Shift End Time", datetime.time(15, 0))
                
                took_lunch = st.checkbox("Did you take a lunch? (Deducts 0.5 hrs)", value=False)
                
                # Calculate duration
                start_dt = datetime.datetime.combine(datetime.date.today(), start_time)
                end_dt = datetime.datetime.combine(datetime.date.today(), end_time)
                if end_dt <= start_dt:
                    end_dt += datetime.timedelta(days=1)
                
                shift_duration = (end_dt - start_dt).total_seconds() / 3600.0
                if took_lunch:
                    shift_duration = max(0.0, shift_duration - 0.5)
                
                st.info(f"**Calculated Shift Duration:** {shift_duration:.2f} hours")
                
                st.subheader("Step 2: Cost Code Allocation")
                st.markdown("Allocate your shift hours across up to 3 cost codes.")
                
                allocations = []
                for i in range(3):
                    st.markdown(f"**Allocation {i+1}**")
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        selected_cc = st.selectbox(f"Cost Code", list(cost_code_options.keys()), key=f"cc_{i}")
                    with c2:
                        alloc_hours = st.number_input(f"Hours", min_value=0.0, step=0.5, value=0.0, key=f"hrs_{i}")
                    alloc_desc = st.text_input(f"Work Description (Optional)", key=f"desc_{i}")
                    allocations.append({
                        "cost_code": selected_cc,
                        "hours": alloc_hours,
                        "description": alloc_desc
                    })
                    st.markdown("---")
            else:
                selected_cost_code = st.selectbox("Cost Code", list(cost_code_options.keys()))
                equipment_df = db.get_equipment()
                equipment_options = dict(zip(equipment_df['display_name'], equipment_df['id']))
                selected_equipment = st.selectbox("Equipment", list(equipment_options.keys()))
                hours = st.number_input("Hours Used", min_value=0.5, step=0.5, value=8.0)
                
            submit = st.form_submit_button("Log Hours", use_container_width=True)
            
            if submit:
                project_id = project_options[selected_project]
                
                if log_type == "Labor":
                    total_allocated = sum(alloc["hours"] for alloc in allocations)
                    
                    if total_allocated == 0:
                        st.error("⚠️ Allocation Error: Total allocated hours cannot be 0.")
                    elif total_allocated != shift_duration:
                        st.error(f"⚠️ Allocation Error: Your allocated hours ({total_allocated} hrs) do not match your total shift duration ({shift_duration} hrs).")
                    else:
                        start_time_str = start_time.strftime("%H:%M")
                        end_time_str = end_time.strftime("%H:%M")
                        
                        for alloc in allocations:
                            if alloc["hours"] > 0:
                                cost_code_id = cost_code_options[alloc["cost_code"]]
                                db.log_labor(log_date, project_id, st.session_state.logged_in_user_id, cost_code_id, alloc["hours"], alloc["description"], start_time_str, end_time_str)
                        st.success(f"Successfully logged {total_allocated} labor hours.")
                else:
                    cost_code_id = cost_code_options[selected_cost_code]
                    eq_id = equipment_options[selected_equipment]
                    db.log_equipment(log_date, project_id, st.session_state.logged_in_user_id, eq_id, cost_code_id, hours)
                    st.success(f"Successfully logged {hours} equipment hours for {selected_equipment}.")

    elif view == "Foreman Review":
        st.header("Foreman Review")
        
        # Get projects for the project specific approve all
        projects_df = db.get_projects()
        project_options = dict(zip(projects_df['project_name'], projects_df['id']))
        selected_project_for_approval = st.selectbox("Select Project for Bulk Approval", list(project_options.keys()))
        
        if st.button("APPROVE ALL PENDING FOR SELECTED PROJECT", use_container_width=True):
            db.approve_all_pending(project_options[selected_project_for_approval])
            st.success(f"Approved all pending logs for {selected_project_for_approval}!")
            st.rerun()

        st.subheader("Pending Labor Logs")
        pending_labor = db.get_pending_labor_logs()
        if pending_labor.empty:
            st.info("No pending labor logs.")
        else:
            for _, row in pending_labor.iterrows():
                with st.container():
                    st.markdown(f"**Date:** {row['Date']} | **Worker:** {row['Worker']}")
                    st.markdown(f"**Project:** {row['Project']} | **Cost Code:** {row['Cost Code']}")
                    st.markdown(f"**Hours:** {row['Hours']} | **Notes:** {row['Description']}")
                    if st.button("Approve Labor", key=f"app_lab_{row['log_id']}"):
                        db.approve_labor_log(row['log_id'])
                        st.rerun()
                    st.markdown("---")

        st.subheader("Pending Equipment Logs")
        pending_eq = db.get_pending_equipment_logs()
        if pending_eq.empty:
            st.info("No pending equipment logs.")
        else:
            for _, row in pending_eq.iterrows():
                with st.container():
                    st.markdown(f"**Date:** {row['Date']} | **Logged By:** {row['Logged By']}")
                    st.markdown(f"**Project:** {row['Project']} | **Cost Code:** {row['Cost Code']}")
                    st.markdown(f"**Equipment:** {row['Equipment Asset']} | **Hours:** {row['Hours']}")
                    if st.button("Approve Equipment", key=f"app_eq_{row['log_id']}"):
                        db.approve_equipment_log(row['log_id'])
                        st.rerun()
                    st.markdown("---")

    elif view == "Office Dashboard":
        if st.session_state.logged_in_user_role != 'Admin':
            st.error("Access Denied")
            st.stop()
            
        st.header("Office Dashboard")
        
        st.subheader("Labor Hours Summary")
        labor_summary = db.get_labor_summary()
        if not labor_summary.empty:
            st.dataframe(labor_summary, use_container_width=True)
            csv_labor = labor_summary.to_csv(index=False).encode('utf-8')
            st.download_button("Export Labor to CSV", csv_labor, "labor_summary.csv", "text/csv", key="labor_csv")
        else:
            st.info("No labor hours logged yet.")
            
        st.subheader("Equipment Hours Summary")
        eq_summary = db.get_equipment_summary()
        if not eq_summary.empty:
            st.dataframe(eq_summary, use_container_width=True)
            csv_eq = eq_summary.to_csv(index=False).encode('utf-8')
            st.download_button("Export Equipment to CSV", csv_eq, "equipment_summary.csv", "text/csv", key="eq_csv")
        else:
            st.info("No equipment hours logged yet.")
            
        with st.expander("⚙️ Employee Permissions & Administration"):
            st.markdown("### Update Existing Permissions")
            admin_emps_df = db.get_employees()
            admin_emp_options = dict(zip(admin_emps_df['full_name'], admin_emps_df['id']))
            selected_admin_emp = st.selectbox("Select Employee", list(admin_emp_options.keys()), key="update_emp")
            new_role = st.selectbox("Assign Role", ["Crew", "Foreman", "Admin"], key="update_role")
            
            if st.button("Update Permissions"):
                emp_id_to_update = admin_emp_options[selected_admin_emp]
                db.update_employee_permissions(emp_id_to_update, new_role)
                st.toast(f"Permissions updated for {selected_admin_emp}!")
                import time; time.sleep(0.5)
                st.rerun()

            st.divider()

            st.markdown("### ➕ Add New Employee")
            with st.form("add_employee_form"):
                new_first_name = st.text_input("First Name")
                new_last_name = st.text_input("Last Name")
                new_emp_email = st.text_input("Email Address")
                new_emp_role = st.selectbox("System Access Role", ["Crew", "Foreman", "Admin"])
                add_emp_submit = st.form_submit_button("ADD EMPLOYEE TO SYSTEM", use_container_width=True)
                
                if add_emp_submit:
                    if not new_first_name or not new_last_name or not new_emp_email:
                        st.error("First Name, Last Name, and Email are required.")
                    else:
                        token = secrets.token_urlsafe(16)
                        db.create_employee_invite(new_first_name, new_last_name, new_emp_email, new_emp_role, token)
                        
                        # Generate the invite link using Streamlit's base URL configuration combined with the token
                        # In many deployments the base URL could be derived from the request, but we will use the standard local format for the demo.
                        invite_link = f"http://localhost:8501/?invite={token}"
                        
                        st.toast(f"Successfully added {new_first_name} {new_last_name} to the system!")
                        st.success(f"**Invitation Link Generated:**\n\n[Click here or copy this link]({invite_link})\n\n`{invite_link}`")
                        print(f"INVITATION LINK FOR {new_emp_email}: {invite_link}")
                        
            st.divider()

            st.markdown("### ❌ Remove Employee From System")
            del_selected_emp = st.selectbox("Select Employee to Remove", list(admin_emp_options.keys()), key="del_emp_select")
            del_confirm = st.checkbox("I confirm I want to permanently delete this employee from the system")
            if st.button("PERMANENTLY DELETE EMPLOYEE", use_container_width=True):
                if not del_confirm:
                    st.warning("You must check the confirmation box to delete an employee.")
                else:
                    emp_id_to_delete = admin_emp_options[del_selected_emp]
                    success, message = db.delete_employee(emp_id_to_delete)
                    if success:
                        st.toast(f"Successfully deleted {del_selected_emp}!")
                        import time; time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(message)
