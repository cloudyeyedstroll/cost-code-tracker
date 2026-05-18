import streamlit as st
import datetime
import io
from dotenv import load_dotenv
import database as db
import reporting
import secrets
from streamlit_drawable_canvas import st_canvas
import base64
import time
import ai_vision

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

# Check for password recovery flow
is_recovery = st.query_params.get("type") == "recovery"
if is_recovery:
    token_hash = st.query_params.get("token_hash")
    
    if not token_hash:
        st.error("Missing recovery token. Please request a new password reset link.")
        if st.button("Return to Login"):
            st.query_params.clear()
            st.rerun()
        st.stop()
        
    st.header("🔒 Set New Password")
    st.write("Please set up a secure new password for your account.")
    
    with st.form("recovery_form"):
        new_password = st.text_input("Enter New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        submit_recovery = st.form_submit_button("UPDATE PASSWORD", use_container_width=True)
        
        if submit_recovery:
            if not new_password or not confirm_password:
                st.error("Please fill in all fields.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            elif len(new_password) < 6:
                st.error("Password must be at least 6 characters long.")
            else:
                try:
                    # First verify the token hash to establish the session
                    verify_res = db.supabase.auth.verify_otp({"token_hash": token_hash, "type": "recovery"})
                    
                    if verify_res.session:
                        # Once session is established, update the user password
                        db.supabase.auth.update_user({"password": new_password})
                        st.query_params.clear()
                        st.success("Password updated successfully! You can now log in.")
                        import time; time.sleep(1.5)
                        st.rerun()
                    else:
                        st.error("Failed to verify the recovery token. It may have expired.")
                except Exception as e:
                    st.error(f"Failed to update password. The link may have expired. Error: {e}")
    st.stop()

# Check for native Supabase invite token hash
if "token_hash" in st.query_params and not is_recovery:
    token_hash = st.query_params.get("token_hash")
    
    # Immediately verify the hash
    is_valid, user = db.verify_invite_hash(token_hash)
    
    if not is_valid:
        st.query_params.clear()
        st.error("This invitation link is invalid or has expired.")
        if st.button("Return to Login"):
            st.rerun()
        st.stop()
        
    st.header("🔐 Activate Your Mobile Account")
    st.write("Welcome! Please set up a secure password to activate your time card access.")
    
    with st.form("activation_form"):
        new_password = st.text_input("Create Secure Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submit_activation = st.form_submit_button("ACTIVATE TIME CARD ACCESS", use_container_width=True)
        
        if submit_activation:
            if not new_password or not confirm_password:
                st.error("Please fill in all fields.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            elif len(new_password) < 6:
                st.error("Password must be at least 6 characters long.")
            else:
                success = db.activate_employee_account(new_password)
                if success:
                    st.query_params.clear()
                    st.success("Account activated successfully! You can now log in.")
                    import time; time.sleep(1.5)
                    st.rerun()
                else:
                    st.error("Failed to activate account. The session may have expired.")
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
    
    email = st.text_input("Email Address")
    forgot_mode = st.toggle("Forgot Password?", value=False)
    
    if forgot_mode:
        st.info("Enter your registered email address above to receive a secure password reset link.")
        submit_reset = st.button("SEND RESET LINK", type="primary", use_container_width=True)
        if submit_reset:
            clean_email = email.strip()
            if not clean_email:
                st.error("Please enter an email address first.")
            else:
                res = db.send_password_reset_email(clean_email)
                if res is True:
                    st.success("Recovery email sent! Check your inbox.")
                else:
                    st.error(f"Error sending recovery email: {res}")
    else:
        password = st.text_input("Password", type="password")
        submit_login = st.button("LOG IN", type="primary", use_container_width=True)
        
        if submit_login:
            clean_email = email.strip()
            if not clean_email or not password:
                st.error("Please enter both email and password. (Note: If using mobile autofill, tap anywhere outside the password box before tapping LOG IN to ensure the password registers).")
            else:
                emp_data = db.verify_employee_login(clean_email, password)
                if emp_data:
                    if "error" in emp_data:
                        # Supabase often returns a generic error if credentials are wrong, 
                        # but we can pass it through.
                        st.error(f"System Error: {emp_data['error']}")
                    else:
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
        view = st.selectbox("Select View", ["Field Logging", "Foreman Review", "📋 Force Account Sign-off"])
    elif role == 'Admin':
        view = st.selectbox("Select View", ["Field Logging", "Foreman Review", "📋 Force Account Sign-off", "Office Dashboard"])

    if view == "Field Logging":
        st.header("Log Field Hours")
        
        log_type = st.radio("Log Type", ["Labor", "Equipment"], horizontal=True)
        
        projects_df = db.get_projects()
        
        if 'form_reset_key' not in st.session_state:
            st.session_state.form_reset_key = 0
            
        hist_key = f"hist_{st.session_state.form_reset_key}"
        if hist_key not in st.session_state:
            historical_logs = db.get_latest_user_logs(st.session_state.logged_in_user_id)
            st.session_state[hist_key] = historical_logs
            
        if 'alloc_ids' not in st.session_state:
            st.session_state.alloc_ids = [0]
            st.session_state.next_alloc_id = 1

        prefix = f"fk_{st.session_state.form_reset_key}_"
        
        log_date = st.date_input("Date", datetime.date.today(), key=f"{prefix}date")
        
        project_options = dict(zip(projects_df['display_name'], projects_df['id']))
        project_list = list(project_options.keys())
        default_proj_idx = 0
        hist_proj_id = st.session_state[hist_key].get('project_id')
        if hist_proj_id:
            for i, (name, pid) in enumerate(project_options.items()):
                if pid == hist_proj_id:
                    default_proj_idx = i
                    break
                    
        selected_project = st.selectbox("Project", project_list, index=default_proj_idx, key=f"{prefix}proj")
        project_id = project_options[selected_project]
        
        # Fetch cost codes specific to the selected project
        cost_codes_df = db.get_cost_codes(project_id)
        cost_code_options = dict(zip(cost_codes_df['display_name'], cost_codes_df['id']))
        cc_list = list(cost_code_options.keys())
        default_cc_idx = 0
        hist_cc_id = st.session_state[hist_key].get('cost_code_id')
        if hist_cc_id:
            for i, (name, cc_id) in enumerate(cost_code_options.items()):
                if cc_id == hist_cc_id:
                    default_cc_idx = i
                    break
        
        if log_type == "Labor":
            st.subheader("Step 1: Shift Time Entry")
            col1, col2 = st.columns(2)
            with col1:
                start_time = st.time_input("Shift Start Time", datetime.time(7, 0), key=f"{prefix}start")
            with col2:
                end_time = st.time_input("Shift End Time", datetime.time(15, 0), key=f"{prefix}end")
            
            took_lunch = st.checkbox("Did you take a lunch? (Deducts 0.5 hrs)", value=False, key=f"{prefix}lunch")
            
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
            st.markdown("Allocate your shift hours across multiple cost codes.")
            
            allocations = []
            for i, alloc_id in enumerate(st.session_state.alloc_ids):
                c_head, c_del = st.columns([5, 1])
                with c_head:
                    st.markdown(f"**Allocation {i+1}**")
                with c_del:
                    if len(st.session_state.alloc_ids) > 1:
                        if st.button("🗑️ Remove", key=f"{prefix}del_{alloc_id}"):
                            st.session_state.alloc_ids.remove(alloc_id)
                            st.rerun()
                            
                c1, c2 = st.columns([2, 1])
                with c1:
                    selected_cc = st.selectbox(f"Cost Code", cc_list, index=default_cc_idx, key=f"{prefix}cc_{alloc_id}")
                with c2:
                    alloc_hours = st.number_input(f"Hours", min_value=0.0, step=0.5, value=0.0, key=f"{prefix}hrs_{alloc_id}")
                alloc_desc = st.text_input(f"Work Description (Optional)", key=f"{prefix}desc_{alloc_id}")
                allocations.append({
                    "cost_code": selected_cc,
                    "hours": alloc_hours,
                    "description": alloc_desc
                })
                st.markdown("---")
            
            if st.button("➕ Add Another Cost Code"):
                st.session_state.alloc_ids.append(st.session_state.next_alloc_id)
                st.session_state.next_alloc_id += 1
                st.rerun()
                
        else:
            selected_cost_code = st.selectbox("Cost Code", cc_list, index=default_cc_idx, key=f"{prefix}eq_cc")
            equipment_df = db.get_equipment(project_id)
            equipment_options = dict(zip(equipment_df['display_name'], equipment_df['id']))
            eq_list = list(equipment_options.keys())
            default_eq_idx = 0
            hist_eq_id = st.session_state[hist_key].get('equipment_id')
            if hist_eq_id:
                for i, (name, eq_id) in enumerate(equipment_options.items()):
                    if eq_id == hist_eq_id:
                        default_eq_idx = i
                        break
            selected_equipment = st.selectbox("Equipment", eq_list, index=default_eq_idx, key=f"{prefix}eq_sel")
            
            selected_equip_id = equipment_options[selected_equipment]
            latest_end_meter = db.get_latest_equipment_meter(selected_equip_id) or 0.0
            
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                start_meter = st.number_input("Starting Machine Hours", min_value=0.0, step=0.1, value=float(latest_end_meter), key=f"{prefix}eq_start")
            with col_m2:
                end_meter = st.number_input("Ending Machine Hours", min_value=0.0, step=0.1, value=float(latest_end_meter), key=f"{prefix}eq_end")
            
        submit = st.button("Log Hours", type="primary", use_container_width=True)
        
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
                    st.session_state.alloc_ids = [0]
                    st.session_state.next_alloc_id = 1
                    st.session_state.form_reset_key += 1
                    st.rerun()
            else:
                if end_meter < start_meter:
                    st.error("Ending machine hours cannot be less than starting hours.")
                    st.stop()
                runtime = end_meter - start_meter
                cost_code_id = cost_code_options[selected_cost_code]
                eq_id = equipment_options[selected_equipment]
                db.log_equipment(log_date, project_id, st.session_state.logged_in_user_id, eq_id, cost_code_id, hours_used=runtime, start_meter=start_meter, end_meter=end_meter, calculated_runtime=runtime)
                st.success(f"Successfully logged {runtime:.1f} equipment hours for {selected_equipment}.")
                st.session_state.alloc_ids = [0]
                st.session_state.next_alloc_id = 1
                st.session_state.form_reset_key += 1
                st.rerun()
                
        with st.expander("🚛 Materials Tracker & Ticket Scanner"):
            st.subheader("Log Material Yields")
            ticket_file = st.file_uploader("Upload Delivery Ticket (Optional)", type=['jpg', 'jpeg', 'png', 'webp'], key=f"{prefix}ticket")
            
            extracted_data = {}
            if ticket_file is not None:
                if st.button("🔍 AI Analyze Ticket"):
                    with st.spinner("Analyzing with Vision AI..."):
                        try:
                            bytes_data = ticket_file.getvalue()
                            dt = ai_vision.extract_ticket_data(bytes_data)
                            extracted_data = dt.model_dump()
                            st.success("Ticket parsed successfully!")
                        except Exception as e:
                            st.error(f"Error parsing ticket: {e}")
            
            mat_proj = st.selectbox("Project", project_list, index=default_proj_idx, key=f"{prefix}mat_proj")
            mat_cc = st.selectbox("Cost Code", cc_list, index=default_cc_idx, key=f"{prefix}mat_cc")
            mat_type = st.radio("Log Type", ["Material Used", "Import/Export Spoil"], key=f"{prefix}mat_type")
            mat_supplier = st.text_input("Supplier/Quarry", value=extracted_data.get('supplier', ''), key=f"{prefix}mat_sup")
            mat_desc = st.text_input("Material Description", value=extracted_data.get('material_description', ''), key=f"{prefix}mat_desc")
            c1, c2 = st.columns(2)
            with c1:
                mat_qty = st.number_input("Quantity", value=float(extracted_data.get('quantity', 0.0)), key=f"{prefix}mat_qty")
            with c2:
                mat_unit = st.text_input("Unit (e.g. Tons, CY)", value=extracted_data.get('unit', ''), key=f"{prefix}mat_unit")
            
            if st.button("Submit Material Log", type="primary", key=f"{prefix}mat_sub"):
                proj_id = project_options[mat_proj]
                cc_id = cost_code_options[mat_cc]
                ticket_url = None
                if ticket_file:
                    ticket_url = db.upload_ticket_image(ticket_file.getvalue(), ticket_file.name)
                success = db.log_material(proj_id, st.session_state.logged_in_user_id, cc_id, log_date, mat_type, mat_supplier, mat_desc, mat_qty, mat_unit, ticket_url)
                if success:
                    st.success("Material logged successfully!")
                    time.sleep(1)
                    st.rerun()

        with st.expander("👷 Subcontractor Tracker"):
            st.subheader("Log Subcontractor Activity")
            
            sub_ticket_file = st.file_uploader("⚡ AI Subcontractor Ticket Scan (Capture Photo)", type=["jpg", "jpeg", "png"], key=f"{prefix}sub_img")
            
            sub_scan_state_key = f"{prefix}sub_scan_state"
            if sub_scan_state_key not in st.session_state:
                st.session_state[sub_scan_state_key] = {}
                
            if sub_ticket_file is not None:
                if st.button("Scan Subcontractor Ticket", key=f"{prefix}sub_scan_btn"):
                    with st.spinner("AI parsing subcontractor sheet..."):
                        try:
                            ticket_data = ai_vision.extract_subcontractor_ticket(sub_ticket_file.getvalue())
                            st.session_state[sub_scan_state_key] = {
                                "company": ticket_data.company_name or "",
                                "scope": ticket_data.scope_of_work or "",
                                "hours": ticket_data.hours_worked or 0.0,
                                "ticket_no": ticket_data.ticket_number or ""
                            }
                            st.success("✅ Extracted data from ticket!")
                        except Exception as e:
                            st.error(f"Error parsing ticket: {e}")
            
            sub_state = st.session_state.get(sub_scan_state_key, {})
            
            sub_proj = st.selectbox("Project", project_list, index=default_proj_idx, key=f"{prefix}sub_proj")
            sub_cc = st.selectbox("Cost Code", cc_list, index=default_cc_idx, key=f"{prefix}sub_cc")
            
            sub_company = st.text_input("Company Name", value=sub_state.get("company", ""), key=f"{prefix}sub_comp")
            sub_ticket_no = st.text_input("Ticket Number", value=sub_state.get("ticket_no", ""), key=f"{prefix}sub_tno")
            sub_scope = st.text_area("Scope of Work", value=sub_state.get("scope", ""), key=f"{prefix}sub_scope")
            sub_hours = st.number_input("Total Hours Worked (Crew)", min_value=0.0, step=0.5, value=float(sub_state.get("hours", 0.0)), key=f"{prefix}sub_hrs")
            sub_comments = st.text_input("Comments", key=f"{prefix}sub_comments")
            
            if st.button("Submit Subcontractor Log", type="primary", key=f"{prefix}sub_sub"):
                proj_id = project_options[sub_proj]
                cc_id = cost_code_options[sub_cc]
                
                ticket_url = None
                if sub_ticket_file:
                    with st.spinner("Uploading image..."):
                        ticket_url = db.upload_ticket_image(sub_ticket_file.getvalue(), sub_ticket_file.name)
                        
                if db.log_subcontractor(proj_id, st.session_state.logged_in_user_id, cc_id, log_date, sub_company, sub_scope, sub_hours, sub_comments, sub_ticket_no, ticket_url):
                    st.success("Subcontractor activity logged successfully!")
                    st.session_state[sub_scan_state_key] = {} # Clear state
                    time.sleep(1)
                    st.rerun()

        st.divider()
        start_date, end_date = db.get_current_pay_period()
        st.subheader("Your Timecard Summary")
        st.markdown(f"**Current Pay Period:** {start_date} to {end_date}")
        summary_data = db.get_employee_timecard_summary(st.session_state.logged_in_user_id, start_date, end_date)
        col_app, col_pen = st.columns(2)
        col_app.metric("Approved Hours", f"{summary_data['Approved']:.1f}")
        col_pen.metric("Pending Hours", f"{summary_data['Pending']:.1f}")

    elif view == "Foreman Review":
        st.header("Foreman Review")
        
        # Get projects for the project specific approve all
        projects_df = db.get_projects()
        project_options = dict(zip(projects_df['display_name'], projects_df['id']))
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

    elif view == "📋 Force Account Sign-off":
        if st.session_state.logged_in_user_role not in ['Foreman', 'Admin']:
            st.error("Access Denied")
            st.stop()
        
        st.header("📋 Force Account Sign-off")
        st.markdown("Review and obtain client signature for Time & Materials (Cost Code 99-000) labor and equipment logs.")
        
        projects_df = db.get_projects()
        if projects_df.empty:
            st.warning("No projects available.")
        else:
            project_options = dict(zip(projects_df['display_name'], projects_df['id']))
            selected_project = st.selectbox("Select Project for T&M Sign-off", list(project_options.keys()))
            proj_id = project_options[selected_project]
            
            l_logs, eq_logs = db.get_unsigned_tm_logs(proj_id)
            
            if not l_logs and not eq_logs:
                st.info("No unsigned T&M logs for this project.")
            else:
                st.subheader("Unsigned T&M Logs")
                if l_logs:
                    st.markdown("**Labor Logs**")
                    import pandas as pd
                    st.dataframe(pd.DataFrame(l_logs)[['date', 'worker_name', 'hours_worked', 'work_description']], use_container_width=True)
                if eq_logs:
                    st.markdown("**Equipment Logs**")
                    st.dataframe(pd.DataFrame(eq_logs)[['date', 'equipment_name', 'hours_used']], use_container_width=True)
                
                with st.form("fa_signoff_form"):
                    client_rep = st.text_input("Client Representative Name")
                    
                    st.markdown("**Client Signature**")
                    canvas_result = st_canvas(
                        fill_color="rgba(255, 165, 0, 0.3)",
                        stroke_width=3,
                        stroke_color="#000000",
                        background_color="#EEEEEE",
                        update_streamlit=True,
                        height=200,
                        drawing_mode="freedraw",
                        key="canvas",
                    )
                    
                    submit_signoff = st.form_submit_button("SUBMIT FORCE ACCOUNT SIGN-OFF")
                    
                    if submit_signoff:
                        if not client_rep:
                            st.error("Client Representative Name is required.")
                        elif canvas_result.image_data is None:
                            st.error("Signature is required.")
                        else:
                            import numpy as np
                            from PIL import Image
                            from io import BytesIO
                            
                            # Convert from rgba to rgb
                            img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                            # Check if the canvas is actually drawn on (not completely empty)
                            if not np.any(canvas_result.image_data[:, :, 3]):
                                st.error("Please provide a signature.")
                            else:
                                bg = Image.new("RGB", img.size, (255, 255, 255))
                                bg.paste(img, mask=img.split()[3])
                                
                                buffered = BytesIO()
                                bg.save(buffered, format="PNG")
                                img_str = base64.b64encode(buffered.getvalue()).decode()
                                
                                l_ids = [l['id'] for l in l_logs]
                                eq_ids = [e['id'] for e in eq_logs]
                                
                                db.create_force_account(proj_id, client_rep, img_str, l_ids, eq_ids)
                                st.success("Force Account submitted successfully!")
                                import time; time.sleep(1)
                                st.rerun()

    elif view == "Office Dashboard":
        if st.session_state.logged_in_user_role != 'Admin':
            st.error("Access Denied")
            st.stop()
            
        st.header("Office Dashboard")
        
        projects_df = db.get_projects()
        filter_options = ["✨ All Active Projects"]
        if not projects_df.empty:
            filter_options += projects_df['display_name'].tolist()
            
        selected_project_filter = st.selectbox("Filter Dashboard by Project", options=filter_options)
        
        st.markdown("---")
        st.subheader("📄 Automated Daily Reporting")
        col_rp1, col_rp2 = st.columns([1, 2])
        with col_rp1:
            report_date = st.date_input("Select Report Date", value=datetime.date.today(), key="report_date")
        with col_rp2:
            st.write("")
            st.write("")
            if selected_project_filter == "✨ All Active Projects":
                st.warning("Please select a specific project to generate a daily report.")
            else:
                if st.button("📥 Download Daily PDF Report", use_container_width=True):
                    with st.spinner("Assembling production layout sheets..."):
                        # Get project id from display name
                        proj_id = None
                        for _, row in projects_df.iterrows():
                            if row['display_name'] == selected_project_filter:
                                proj_id = row['id']
                                break
                        
                        if proj_id:
                            pdf_buffer = reporting.build_daily_pdf_buffer(proj_id, report_date)
                            if pdf_buffer:
                                st.download_button(
                                    label="Download PDF Now",
                                    data=pdf_buffer,
                                    file_name=f"Daily_Report_{selected_project_filter}_{report_date}.pdf",
                                    mime="application/pdf",
                                    use_container_width=True
                                )
                                st.success("Report generated successfully! Click above to download.")
                            else:
                                st.info("No timecards or logs submitted for this selected operational date.")
        st.markdown("---")
        
        st.subheader("Labor Hours Summary")
        labor_summary = db.get_labor_summary()
        if not labor_summary.empty:
            if selected_project_filter != "✨ All Active Projects":
                labor_summary = labor_summary[labor_summary['Project'] == selected_project_filter]
                
            if not labor_summary.empty:
                st.dataframe(labor_summary, use_container_width=True)
                csv_labor = labor_summary.to_csv(index=False).encode('utf-8')
                st.download_button("Export Labor to CSV", csv_labor, "labor_summary.csv", "text/csv", key="labor_csv")
            else:
                st.info(f"No labor hours logged for {selected_project_filter}.")
        else:
            st.info("No labor hours logged yet.")
            
        st.subheader("Equipment Hours Summary")
        eq_summary = db.get_equipment_summary()
        if not eq_summary.empty:
            if selected_project_filter != "✨ All Active Projects":
                eq_summary = eq_summary[eq_summary['Project'] == selected_project_filter]
                
            if not eq_summary.empty:
                st.dataframe(eq_summary, use_container_width=True)
                csv_eq = eq_summary.to_csv(index=False).encode('utf-8')
                st.download_button("Export Equipment to CSV", csv_eq, "equipment_summary.csv", "text/csv", key="eq_csv")
            else:
                st.info(f"No equipment hours logged for {selected_project_filter}.")
        else:
            st.info("No equipment hours logged yet.")

        st.subheader("📋 Signed Force Accounts")
        fa_df = db.get_signed_force_accounts()
        if not fa_df.empty:
            if selected_project_filter != "✨ All Active Projects":
                fa_df = fa_df[fa_df['Project'] == selected_project_filter]
                
            if not fa_df.empty:
                for _, row in fa_df.iterrows():
                    with st.expander(f"Ticket #{row['id']} - {row['Project']} - {row['date']}"):
                        st.markdown(f"**Client Representative:** {row['client_representative']}")
                        img_data = base64.b64decode(row['signature_data'])
                        st.image(img_data, caption="Client Signature")
            else:
                st.info(f"No signed Force Accounts for {selected_project_filter}.")
        else:
            st.info("No signed Force Accounts yet.")
            
        st.subheader("🚛 Materials & Yields Summary")
        mat_summary = db.get_all_material_logs()
        if not mat_summary.empty:
            if selected_project_filter != "✨ All Active Projects":
                mat_summary = mat_summary[mat_summary['Project'] == selected_project_filter]
                
            if not mat_summary.empty:
                st.dataframe(mat_summary, use_container_width=True, column_config={"Ticket URL": st.column_config.LinkColumn("Ticket Link")})
                csv_mat = mat_summary.to_csv(index=False).encode('utf-8')
                st.download_button("Export Materials to CSV", csv_mat, "materials_summary.csv", "text/csv", key="mat_csv")
            else:
                st.info(f"No material logs for {selected_project_filter}.")
        else:
            st.info("No material logs yet.")

        st.subheader("👷 Subcontractor Summary")
        sub_summary = db.get_all_subcontractor_logs()
        if not sub_summary.empty:
            if selected_project_filter != "✨ All Active Projects":
                sub_summary = sub_summary[sub_summary['Project'] == selected_project_filter]
                
            if not sub_summary.empty:
                st.dataframe(sub_summary, use_container_width=True)
                csv_sub = sub_summary.to_csv(index=False).encode('utf-8')
                st.download_button("Export Subcontractors to CSV", csv_sub, "subcontractor_summary.csv", "text/csv", key="sub_csv")
            else:
                st.info(f"No subcontractor logs for {selected_project_filter}.")
        else:
            st.info("No subcontractor logs yet.")
            

        with st.expander("⚙️ Employee Permissions & Administration"):
            job_titles_df = db.get_all_job_titles()
            job_title_options = job_titles_df['title_name'].tolist() if not job_titles_df.empty else ["Crew", "Foreman", "Admin"]
            
            st.markdown("### ✨ Manage Custom Job Titles")
            with st.form("add_job_title_form"):
                col1, col2 = st.columns(2)
                with col1:
                    new_title_name = st.text_input("Custom Job Title (e.g. Project Manager)")
                with col2:
                    new_title_tier = st.selectbox("Permission Tier", ["Crew", "Foreman", "Admin"])
                
                add_title_submit = st.form_submit_button("CREATE JOB TITLE", use_container_width=True)
                if add_title_submit:
                    if not new_title_name:
                        st.error("Job title is required.")
                    else:
                        success, msg = db.add_custom_job_title(new_title_name, new_title_tier)
                        if success:
                            st.toast(f"Successfully created '{new_title_name}'!")
                            import time; time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error(f"Failed to create job title: {msg}")
            
            st.divider()

            st.markdown("### Update Existing Permissions")
            admin_emps_df = db.get_employees()
            admin_emp_options = dict(zip(admin_emps_df['full_name'], admin_emps_df['id']))
            selected_admin_emp = st.selectbox("Select Employee", list(admin_emp_options.keys()), key="update_emp")
            new_role = st.selectbox("Assign Job Title", job_title_options, key="update_role")
            
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
                new_emp_role = st.selectbox("System Access Role (Job Title)", job_title_options)
                add_emp_submit = st.form_submit_button("ADD EMPLOYEE TO SYSTEM", use_container_width=True)
                
                if add_emp_submit:
                    if not new_first_name or not new_last_name or not new_emp_email:
                        st.error("First Name, Last Name, and Email are required.")
                    else:
                        auth_id = db.create_employee_invite(new_first_name, new_last_name, new_emp_email, new_emp_role)
                        
                        if auth_id:
                            st.toast(f"Successfully added {new_first_name} {new_last_name} to the system!")
                            st.success(f"📩 SiteDocs-style invitation successfully dispatched to {new_emp_email} via Supabase Auth.")
                        else:
                            st.error("Failed to create user or dispatch invitation. Ensure they don't already exist or check configuration.")
                        
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

        with st.expander("🏗️ Project & Job Management", expanded=False):
            st.subheader("SECTION A: Initialize New Job Site")
            with st.form("add_project_form"):
                new_job_number = st.text_input("Job Number (e.g., 25-C13)")
                new_project_name = st.text_input("Project / Job Name (e.g., 1st and Clark)")
                new_project_location = st.text_input("Project Location / Town (e.g., Chilliwack, BC)")
                add_proj_submit = st.form_submit_button("DEPLOY NEW PROJECT", use_container_width=True)
                
                if add_proj_submit:
                    if not new_job_number or not new_project_name or not new_project_location:
                        st.error("Job Number, Project Name, and Location are required.")
                    else:
                        success, msg = db.add_project(new_job_number, new_project_name, new_project_location)
                        if success:
                            st.toast("🏗️ New project successfully initialized and pushed live to field crews!")
                            import time; time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error(f"Failed to create project: {msg}")

            st.markdown("---")
            
            st.subheader("SECTION B: Manage Cost Codes & Project Scopes")
            st.markdown("Create new cost codes individually or import them via bulk spreadsheet uploads.")
            code_tabs = st.tabs(["➕ Add Single Code Manually", "📁 Bulk Import from Spreadsheet"])
            
            with code_tabs[0]:
                with st.form("manual_cc_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        cc_code = st.text_input("Cost Code / Scope Key", placeholder="e.g., 02-300 or OFF-WATER")
                    with col2:
                        cc_desc = st.text_input("Scope Description", placeholder="e.g., Off-site Watermain Installation")
                    
                    submit_cc = st.form_submit_button("SAVE SINGLE COST CODE")
                    if submit_cc:
                        if not cc_code or not cc_desc:
                            st.error("Both code and description are required.")
                        else:
                            success, msg = db.insert_single_cost_code(cc_code, cc_desc)
                            if success:
                                st.toast(f"Successfully created {cc_code}!")
                                import time; time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error(msg)
            
            with code_tabs[1]:
                st.markdown("> **Note:** The uploaded CSV file must contain headers named exactly `code` and `description`.")
                uploaded_file = st.file_uploader("Upload Cost Code CSV", type=["csv"])
                
                if uploaded_file is not None:
                    import pandas as pd
                    try:
                        df_cc = pd.read_csv(uploaded_file)
                        st.dataframe(df_cc.head(5), use_container_width=True)
                        
                        if st.button("BULK IMPORT CODES"):
                            success, msg = db.bulk_insert_cost_codes(df_cc)
                            if success:
                                st.toast(msg)
                                import time; time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error(msg)
                    except Exception as e:
                        st.error(f"Error parsing CSV: {e}")

        with st.expander("🚜 Fleet & Equipment Management", expanded=False):
            col_eq_l, col_eq_r = st.columns([3, 2])
            
            with col_eq_l:
                st.subheader("📊 Active Fleet Inventory")
                fleet_df = db.get_master_fleet()
                if fleet_df.empty:
                    st.info("No machinery registered yet. Use the registration panel to add assets.")
                else:
                    display_df = fleet_df.copy()
                    rename_cols = {}
                    if 'unit_number' in display_df.columns: rename_cols['unit_number'] = 'Unit #'
                    if 'make' in display_df.columns: rename_cols['make'] = 'Make'
                    if 'model' in display_df.columns: rename_cols['model'] = 'Model'
                    if 'starting_hours' in display_df.columns: rename_cols['starting_hours'] = 'Baseline Hours'
                    
                    display_df = display_df.rename(columns=rename_cols)
                    display_cols = [c for c in ['Unit #', 'Make', 'Model', 'Baseline Hours'] if c in display_df.columns]
                    if display_cols:
                        st.dataframe(display_df[display_cols], use_container_width=True, hide_index=True)
                    else:
                        st.dataframe(display_df, use_container_width=True, hide_index=True)
                        
            with col_eq_r:
                st.subheader("➕ Register New Machinery Asset")
                with st.form("new_equipment_form"):
                    new_unit_number = st.text_input("Unit Number", placeholder="e.g., EX-245 or SK-08")
                    new_make = st.text_input("Manufacturer / Make", placeholder="e.g., John Deere, Cat")
                    new_model = st.text_input("Model Number", placeholder="e.g., 245G, 299D3")
                    new_starting_hours = st.number_input("Current Machine Hours (SMU Baseline)", min_value=0.0, step=0.1)
                    
                    submit_new_eq = st.form_submit_button("REGISTER ASSET", use_container_width=True)
                    if submit_new_eq:
                        if not new_unit_number:
                            st.error("Unit Number is required.")
                        else:
                            success, msg = db.insert_new_equipment(new_unit_number, new_make, new_model, new_starting_hours)
                            if success:
                                st.toast("✅ Asset registered successfully!")
                                import time; time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error(msg)
                                
                st.markdown("---")
                st.subheader("🗑️ Remove Machinery Asset")
                if not fleet_df.empty:
                    with st.form("delete_equipment_form"):
                        unit_numbers = fleet_df['unit_number'].astype(str).tolist() if 'unit_number' in fleet_df.columns else []
                        del_unit_number = st.selectbox("Select Unit to Remove", options=[""] + unit_numbers)
                        submit_delete_eq = st.form_submit_button("REMOVE ASSET", use_container_width=True)
                        if submit_delete_eq:
                            if not del_unit_number:
                                st.error("Please select a unit to remove.")
                            else:
                                success, msg = db.delete_equipment(del_unit_number)
                                if success:
                                    st.toast(f"✅ {msg}")
                                    import time; time.sleep(0.5)
                                    st.rerun()
                                else:
                                    st.error(msg)
                else:
                    st.info("No assets to remove.")

        with st.expander("📅 Payroll & Pay Period Setup"):
            st.markdown("### Manage Active Payroll Cycle")
            curr_start, curr_end = db.get_current_pay_period()
            try:
                curr_start_date = datetime.datetime.strptime(curr_start, "%Y-%m-%d").date()
                curr_end_date = datetime.datetime.strptime(curr_end, "%Y-%m-%d").date()
            except:
                curr_start_date = datetime.date.today() - datetime.timedelta(days=13)
                curr_end_date = datetime.date.today()
            
            with st.form("pay_period_form"):
                col1, col2 = st.columns(2)
                with col1:
                    new_start_date = st.date_input("Pay Period Start Date", value=curr_start_date)
                with col2:
                    new_end_date = st.date_input("Pay Period End Date", value=curr_end_date)
                
                pay_period_submit = st.form_submit_button("SET ACTIVE PAY PERIOD", use_container_width=True)
                
                if pay_period_submit:
                    success = db.update_current_pay_period(new_start_date, new_end_date)
                    if success:
                        st.toast("📅 Global pay period updated successfully!")
                        import time; time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Failed to update pay period.")

        with st.expander("🔌 Connected Integrations Hub"):
            st.markdown("### 🔗 External API Connections")
            settings = db.get_integration_settings() or {}
            
            with st.form("integrations_form"):
                p_client_id = st.text_input("Procore Client ID", value=settings.get("procore_client_id", ""), type="password")
                p_client_secret = st.text_input("Procore Client Secret", value=settings.get("procore_client_secret", ""), type="password")
                v_ai_key = st.text_input("Gemini Vision AI Key", value=settings.get("vision_ai_key", ""), type="password")
                o_api_key = st.text_input("OpenAI API Key (Optional)", value=settings.get("openai_api_key", ""), type="password")
                
                if not p_client_id and not p_client_secret:
                    st.info("⚠️ Connected - Schema Staged for Sync")
                    
                save_integrations = st.form_submit_button("SAVE CONNECTIONS", use_container_width=True)
                if save_integrations:
                    success = db.save_integration_settings(p_client_id, p_client_secret, v_ai_key, o_api_key)
                    if success:
                        st.toast("✅ Integration settings saved securely!")
                        import time; time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Failed to save integration settings.")

        with st.expander("🏢 Company Settings & Branding"):
            st.markdown("### Upload Company Logo")
            st.info("This logo will be automatically perfectly centered on all generated PDF Daily Reports.")
            uploaded_logo = st.file_uploader("Upload Logo (PNG only)", type=["png"])
            if uploaded_logo is not None:
                if st.button("SAVE LOGO"):
                    with st.spinner("Uploading to secure cloud storage..."):
                        bytes_data = uploaded_logo.getvalue()
                        success = db.upload_company_logo(bytes_data)
                        if success:
                            st.success("✅ Company logo updated securely!")
                        else:
                            st.error("Failed to upload company logo.")
            
            # Show preview if existing
            existing_logo = db.get_company_logo()
            if existing_logo:
                st.markdown("#### Current Active Logo:")
                st.image(existing_logo, width=200)


