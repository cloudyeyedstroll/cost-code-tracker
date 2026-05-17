import pandas as pd
import os
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv, find_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import secrets

from dotenv import load_dotenv, find_dotenv, dotenv_values

env_path = find_dotenv()
load_dotenv(env_path, override=True)
env_vars = dotenv_values(env_path) if env_path else {}

# Check os.environ first, fallback to dotenv parsing, then st.secrets
url: str = os.environ.get("SUPABASE_URL") or env_vars.get("SUPABASE_URL")
if not url:
    try:
        url = st.secrets["SUPABASE_URL"]
    except Exception:
        pass

key: str = os.environ.get("SUPABASE_KEY") or env_vars.get("SUPABASE_KEY")
if not key:
    try:
        key = st.secrets["SUPABASE_KEY"]
    except Exception:
        pass

service_role_key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or env_vars.get("SUPABASE_SERVICE_ROLE_KEY")
if not service_role_key:
    try:
        service_role_key = st.secrets["SUPABASE_SERVICE_ROLE_KEY"]
    except Exception:
        pass

supabase_init_error = None

try:
    supabase: Client = create_client(url, key)
    
    if service_role_key:
        supabase_admin: Client = create_client(url, service_role_key)
    else:
        supabase_admin = None
except Exception as e:
    supabase_init_error = str(e)
    print(f"Failed to initialize Supabase client: {e}")
    supabase = None
    supabase_admin = None

def setup():
    # Supabase handles its own schema, so setup is a no-op locally.
    pass

def init_db():
    pass

def seed_db():
    pass

# Helper queries for UI
def get_projects():
    response = supabase.table('projects').select('id, project_name').execute()
    return pd.DataFrame(response.data) if response.data else pd.DataFrame(columns=['id', 'project_name'])

def add_project(project_name, location):
    try:
        supabase.table('projects').insert({
            "project_name": project_name,
            "location": location,
            "procore_id": None
        }).execute()
        return True, "Project added successfully."
    except Exception as e:
        print(f"Error adding project: {e}")
        return False, str(e)

def get_employees():
    response = supabase.table('employees').select('id, first_name, last_name, role').execute()
    df = pd.DataFrame(response.data) if response.data else pd.DataFrame(columns=['id', 'first_name', 'last_name', 'role'])
    if not df.empty:
        df['full_name'] = df['first_name'] + ' ' + df['last_name']
    return df

def get_equipment():
    response = supabase.table('equipment').select('id, unit_number, make_model').execute()
    df = pd.DataFrame(response.data) if response.data else pd.DataFrame(columns=['id', 'unit_number', 'make_model'])
    if not df.empty:
        df['display_name'] = df['unit_number'] + ' - ' + df['make_model']
    return df

def get_cost_codes():
    response = supabase.table('cost_codes').select('id, code_number, description').execute()
    df = pd.DataFrame(response.data) if response.data else pd.DataFrame(columns=['id', 'code_number', 'description'])
    if not df.empty:
        df['display_name'] = df['code_number'] + ' ' + df['description']
    return df

def get_all_job_titles():
    response = supabase.table('job_titles').select('id, title_name, permission_tier').execute()
    return pd.DataFrame(response.data) if response.data else pd.DataFrame(columns=['id', 'title_name', 'permission_tier'])

def add_custom_job_title(title_name, permission_tier):
    try:
        supabase.table('job_titles').insert({
            "title_name": title_name,
            "permission_tier": permission_tier
        }).execute()
        return True, "Job title added successfully."
    except Exception as e:
        return False, str(e)

def log_labor(date, project_id, employee_id, cost_code_id, hours_worked, work_description="", start_time="", end_time=""):
    supabase.table('labor_logs').insert({
        "date": str(date),
        "project_id": project_id,
        "employee_id": employee_id,
        "cost_code_id": cost_code_id,
        "start_time": start_time,
        "end_time": end_time,
        "hours_worked": hours_worked,
        "work_description": work_description
    }).execute()

def log_equipment(date, project_id, employee_id, equipment_id, cost_code_id, hours_used):
    supabase.table('equipment_logs').insert({
        "date": str(date),
        "project_id": project_id,
        "employee_id": employee_id,
        "equipment_id": equipment_id,
        "cost_code_id": cost_code_id,
        "hours_used": hours_used
    }).execute()

def get_employee_role(employee_id):
    response = supabase.table('employees').select('role').eq('id', employee_id).execute()
    return response.data[0]['role'] if response.data else 'Crew'

def update_employee_permissions(employee_id, new_role):
    supabase.table('employees').update({"role": new_role}).eq('id', employee_id).execute()

def create_employee_invite(first_name, last_name, email, role, token=None):
    if not supabase_admin:
        print("Error: Supabase Admin client is not configured. SUPABASE_SERVICE_ROLE_KEY is required.")
        return None
        
    try:
        # Trigger native Supabase Admin Auth invite
        auth_response = supabase_admin.auth.admin.invite_user_by_email(
            email, 
            options={"data": {"first_name": first_name, "last_name": last_name, "role": role}}
        )
        auth_id = auth_response.user.id
        
        # Insert into our public.employees table
        supabase.table('employees').insert({
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "account_status": "Pending",
            "role": role,
            "auth_id": auth_id
        }).execute()
        return auth_id
    except Exception as e:
        print(f"Error creating employee: {e}")
        return None

def verify_invite_hash(token_hash):
    try:
        # Execute a server-side verification request using the native Supabase GoTrue routing client
        res = supabase.auth.verify_otp({"token_hash": token_hash, "type": "invite"})
        if res.session:
            return True, res.user
    except Exception as e:
        print(f"Token verification error: {e}")
    return False, None

def activate_employee_account(new_password):
    try:
        # User is already authenticated via verify_invite_hash OTP session
        user_res = supabase.auth.get_user()
        if user_res.user:
            user_email = user_res.user.email
            
            # Now we can update their password securely
            supabase.auth.update_user({"password": new_password})
            
            # Update their status in the public.employees table
            supabase.table('employees').update({"account_status": "Active"}).eq('email', user_email).execute()
            
            # Sign out to force standard login
            supabase.auth.sign_out()
            return True
    except Exception as e:
        print(f"Activation error: {e}")
    return False

def delete_employee(employee_id):
    # Check for logs
    labor_res = supabase.table('labor_logs').select('id', count='exact').eq('employee_id', employee_id).execute()
    eq_res = supabase.table('equipment_logs').select('id', count='exact').eq('employee_id', employee_id).execute()
    
    if (labor_res.count and labor_res.count > 0) or (eq_res.count and eq_res.count > 0):
        return False, "Cannot delete employee: they have existing labor or equipment logs."
        
    # Get their auth_id so we can delete them from Auth as well
    emp_res = supabase.table('employees').select('auth_id').eq('id', employee_id).execute()
    if emp_res.data and emp_res.data[0].get('auth_id'):
        try:
            supabase.auth.admin.delete_user(emp_res.data[0]['auth_id'])
        except Exception as e:
            print(f"Error deleting from auth: {e}")
            
    supabase.table('employees').delete().eq('id', employee_id).execute()
    return True, "Employee permanently deleted."

def get_pending_labor_logs():
    res = supabase.table('pending_labor_logs_view').select('*').execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=['log_id', 'Date', 'project_id', 'Project', 'Worker', 'Start Time', 'End Time', 'Cost Code', 'Hours', 'Description'])

def get_pending_equipment_logs():
    # We didn't create a view for this in the schema, so we do a pseudo-join here by fetching tables
    # Or, actually, we can just fetch everything and join in pandas!
    eq_logs = supabase.table('equipment_logs').select('*').eq('status', 'Pending').execute()
    if not eq_logs.data:
        return pd.DataFrame(columns=['log_id', 'Date', 'project_id', 'Project', 'Logged By', 'Equipment Asset', 'Cost Code', 'Hours'])
    
    logs_df = pd.DataFrame(eq_logs.data)
    projs = pd.DataFrame(supabase.table('projects').select('id, project_name').execute().data)
    emps = pd.DataFrame(supabase.table('employees').select('id, first_name, last_name').execute().data)
    eqs = pd.DataFrame(supabase.table('equipment').select('id, unit_number, make_model').execute().data)
    ccs = pd.DataFrame(supabase.table('cost_codes').select('id, code_number, description').execute().data)
    
    # Merge
    df = logs_df.merge(projs, left_on='project_id', right_on='id', suffixes=('', '_p'))
    df = df.merge(emps, left_on='employee_id', right_on='id', suffixes=('', '_e'))
    df = df.merge(eqs, left_on='equipment_id', right_on='id', suffixes=('', '_eq'))
    df = df.merge(ccs, left_on='cost_code_id', right_on='id', suffixes=('', '_c'))
    
    df['Project'] = df['project_name']
    df['Logged By'] = df['first_name'] + ' ' + df['last_name']
    df['Equipment Asset'] = df['unit_number'] + ' - ' + df['make_model']
    df['Cost Code'] = df['code_number'] + ' ' + df['description']
    df['Date'] = df['date']
    df['Hours'] = df['hours_used']
    df['log_id'] = df['id']
    
    return df[['log_id', 'Date', 'project_id', 'Project', 'Logged By', 'Equipment Asset', 'Cost Code', 'Hours']].sort_values('Date', ascending=False)

def approve_labor_log(log_id):
    supabase.table('labor_logs').update({"status": "Approved"}).eq('id', log_id).execute()

def approve_equipment_log(log_id):
    supabase.table('equipment_logs').update({"status": "Approved"}).eq('id', log_id).execute()

def approve_all_pending(project_id):
    supabase.table('labor_logs').update({"status": "Approved"}).eq('project_id', project_id).eq('status', 'Pending').execute()
    supabase.table('equipment_logs').update({"status": "Approved"}).eq('project_id', project_id).eq('status', 'Pending').execute()

def get_labor_summary():
    res = supabase.table('labor_summary_view').select('*').execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=['Date', 'Project', 'Worker', 'Start Time', 'End Time', 'Cost Code', 'Status', 'Total Labor Hours', 'Total Labor Cost ($)', 'Description'])

def get_equipment_summary():
    # No view was created, fetch and join in pandas
    eq_logs = supabase.table('equipment_logs').select('*').execute()
    if not eq_logs.data:
        return pd.DataFrame(columns=['Date', 'Project', 'Equipment Asset', 'Cost Code', 'Status', 'Total Equipment Hours', 'Total Equipment Cost ($)'])
        
    logs_df = pd.DataFrame(eq_logs.data)
    projs = pd.DataFrame(supabase.table('projects').select('id, project_name').execute().data)
    eqs = pd.DataFrame(supabase.table('equipment').select('id, unit_number, make_model, hourly_rate').execute().data)
    ccs = pd.DataFrame(supabase.table('cost_codes').select('id, code_number, description').execute().data)
    
    df = logs_df.merge(projs, left_on='project_id', right_on='id', suffixes=('', '_p'))
    df = df.merge(eqs, left_on='equipment_id', right_on='id', suffixes=('', '_eq'))
    df = df.merge(ccs, left_on='cost_code_id', right_on='id', suffixes=('', '_c'))
    
    df['Project'] = df['project_name']
    df['Equipment Asset'] = df['unit_number'] + ' - ' + df['make_model']
    df['Cost Code'] = df['code_number'] + ' ' + df['description']
    df['Date'] = df['date']
    df['Total Equipment Hours'] = df['hours_used']
    df['Status'] = df['status']
    df['Total Equipment Cost ($)'] = df['hours_used'] * df['hourly_rate']
    
    grouped = df.groupby(['Date', 'Project', 'Equipment Asset', 'Cost Code', 'Status']).agg({
        'Total Equipment Hours': 'sum',
        'Total Equipment Cost ($)': 'sum'
    }).reset_index()
    return grouped.sort_values('Date', ascending=False)

def verify_employee_login(email, password):
    if supabase is None:
        url_status = "Set" if url else "Missing"
        key_status = "Set" if key else "Missing"
        return {"error": f"Database client not initialized. Error: {supabase_init_error}. URL: {url_status}, KEY: {key_status}"}
    try:
        # Authenticate with Supabase Auth
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if res.session:
            emp_res = supabase.table('employees').select('id, first_name, last_name, role, account_status').eq('email', email).execute()
            if emp_res.data and emp_res.data[0]['account_status'] == 'Active':
                emp = emp_res.data[0]
                
                # Resolve permission tier from job_titles table
                job_title_res = supabase.table('job_titles').select('permission_tier').eq('title_name', emp['role']).execute()
                permission_tier = job_title_res.data[0]['permission_tier'] if job_title_res.data else 'Crew'
                
                return {
                    "id": emp['id'], 
                    "first_name": emp['first_name'], 
                    "last_name": emp['last_name'], 
                    "role": permission_tier, 
                    "full_name": f"{emp['first_name']} {emp['last_name']}",
                    "job_title": emp['role']
                }
    except Exception as e:
        print(f"Login error: {e}")
        return {"error": str(e)}
    return None

def get_unsigned_tm_logs(project_id):
    # Fetch 99-000 Cost Code ID
    cc_res = supabase.table('cost_codes').select('id').eq('code_number', '99-000').execute()
    if not cc_res.data:
        return [], []
    cc_id = cc_res.data[0]['id']
    
    # Fetch labor logs
    l_res = supabase.table('labor_logs').select('id, date, hours_worked, work_description, employee_id').eq('project_id', project_id).eq('cost_code_id', cc_id).eq('status', 'Approved').is_('force_account_id', 'null').execute()
    l_data = l_res.data if l_res.data else []
    if l_data:
        emps = {e['id']: f"{e['first_name']} {e['last_name']}" for e in supabase.table('employees').select('id, first_name, last_name').execute().data}
        for log in l_data:
            log['worker_name'] = emps.get(log['employee_id'], 'Unknown')
            
    # Fetch equipment logs
    eq_res = supabase.table('equipment_logs').select('id, date, hours_used, equipment_id').eq('project_id', project_id).eq('cost_code_id', cc_id).eq('status', 'Approved').is_('force_account_id', 'null').execute()
    eq_data = eq_res.data if eq_res.data else []
    if eq_data:
        eqs = {e['id']: f"{e['unit_number']} - {e['make_model']}" for e in supabase.table('equipment').select('id, unit_number, make_model').execute().data}
        for log in eq_data:
            log['equipment_name'] = eqs.get(log['equipment_id'], 'Unknown')
            
    return l_data, eq_data

def create_force_account(project_id, client_name, signature_b64, labor_ids, equipment_ids):
    res = supabase.table('force_accounts').insert({
        "project_id": project_id,
        "client_representative": client_name,
        "signature_data": signature_b64
    }).execute()
    fa_id = res.data[0]['id']
    
    if labor_ids:
        for lid in labor_ids:
            supabase.table('labor_logs').update({"force_account_id": fa_id}).eq('id', lid).execute()
    if equipment_ids:
        for eid in equipment_ids:
            supabase.table('equipment_logs').update({"force_account_id": fa_id}).eq('id', eid).execute()

def get_signed_force_accounts():
    res = supabase.table('force_accounts').select('*').order('date', desc=True).execute()
    if not res.data:
        return pd.DataFrame()
    
    df = pd.DataFrame(res.data)
    projs = pd.DataFrame(supabase.table('projects').select('id, project_name').execute().data)
    df = df.merge(projs, left_on='project_id', right_on='id', suffixes=('', '_p'))
    df['Project'] = df['project_name']
    return df

