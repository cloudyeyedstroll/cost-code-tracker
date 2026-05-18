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

if url: url = url.strip('"').strip("'").strip()
if key: key = key.strip('"').strip("'").strip()
if service_role_key: service_role_key = service_role_key.strip('"').strip("'").strip()

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
    response = supabase.table('projects').select('id, job_number, project_name').execute()
    df = pd.DataFrame(response.data) if response.data else pd.DataFrame(columns=['id', 'job_number', 'project_name'])
    if not df.empty:
        df['display_name'] = df['job_number'].fillna('') + ' ' + df['project_name']
        df['display_name'] = df['display_name'].str.strip()
    return df

def add_project(job_number, project_name, location):
    try:
        supabase.table('projects').insert({
            "job_number": job_number,
            "project_name": project_name,
            "location": location,
            "procore_id": None
        }).execute()
        return True, "Project added successfully."
    except Exception as e:
        print(f"Error adding project: {e}")
        return False, str(e)

def get_current_pay_period():
    try:
        res = supabase.table('payroll_settings').select('*').eq('id', 1).execute()
        if res.data:
            return res.data[0]['current_period_start'], res.data[0]['current_period_end']
    except Exception as e:
        print(f"Error fetching pay period: {e}")
    
    # Fallback range (rolling 14-day window)
    end_date = pd.Timestamp.now().date()
    start_date = end_date - pd.Timedelta(days=13)
    return str(start_date), str(end_date)

def update_current_pay_period(start_date, end_date):
    try:
        res = supabase.table('payroll_settings').select('id').eq('id', 1).execute()
        if res.data:
            supabase.table('payroll_settings').update({
                "current_period_start": str(start_date),
                "current_period_end": str(end_date)
            }).eq('id', 1).execute()
        else:
            supabase.table('payroll_settings').insert({
                "id": 1,
                "current_period_start": str(start_date),
                "current_period_end": str(end_date)
            }).execute()
        return True
    except Exception as e:
        print(f"Error updating pay period: {e}")
        return False

def get_employees():
    response = supabase.table('employees').select('id, first_name, last_name, role').execute()
    df = pd.DataFrame(response.data) if response.data else pd.DataFrame(columns=['id', 'first_name', 'last_name', 'role'])
    if not df.empty:
        df['full_name'] = df['first_name'] + ' ' + df['last_name']
    return df

def get_equipment(project_id=None):
    try:
        if project_id:
            # Check if project has specific equipment mapped
            mapped_res = supabase.table('project_equipment').select('equipment_id').eq('project_id', project_id).execute()
            if mapped_res.data:
                eq_ids = [r['equipment_id'] for r in mapped_res.data]
                response = supabase.table('equipment').select('id, unit_number, make_model').in_('id', eq_ids).execute()
            else:
                # Fallback to all equipment
                response = supabase.table('equipment').select('id, unit_number, make_model').execute()
        else:
            response = supabase.table('equipment').select('id, unit_number, make_model').execute()
            
        df = pd.DataFrame(response.data) if response.data else pd.DataFrame(columns=['id', 'unit_number', 'make_model'])
        if not df.empty:
            df['display_name'] = df['unit_number'] + ' - ' + df['make_model']
        return df
    except Exception as e:
        print(f"Error fetching equipment: {e}")
        return pd.DataFrame(columns=['id', 'unit_number', 'make_model', 'display_name'])

def get_master_fleet():
    try:
        response = supabase.table('equipment').select('*').order('unit_number').execute()
        df = pd.DataFrame(response.data) if response.data else pd.DataFrame()
        return df
    except Exception as e:
        print(f"Error fetching master fleet: {e}")
        return pd.DataFrame()

def insert_new_equipment(unit_number, make, model, starting_hours):
    try:
        supabase.table('equipment').insert({
            "unit_number": unit_number,
            "make": make,
            "model": model,
            "starting_hours": starting_hours
        }).execute()
        return True, "Equipment registered successfully."
    except Exception as e:
        print(f"Error inserting new equipment: {e}")
        return False, "Failed to register equipment. Unit number may already exist."

def delete_equipment(unit_number):
    try:
        supabase.table('equipment').delete().eq('unit_number', unit_number).execute()
        return True, f"Equipment {unit_number} deleted successfully."
    except Exception as e:
        print(f"Error deleting equipment: {e}")
        return False, f"Failed to delete equipment {unit_number}."

def insert_single_cost_code(code, description):
    try:
        # Check if exists to emulate ON CONFLICT
        existing = supabase.table('cost_codes').select('id').eq('code_number', code).execute()
        if existing.data:
            supabase.table('cost_codes').update({'description': description}).eq('code_number', code).execute()
            return True, "Cost code updated successfully."
        else:
            supabase.table('cost_codes').insert({
                "code_number": code,
                "description": description
            }).execute()
            return True, "Cost code created successfully."
    except Exception as e:
        print(f"Error inserting cost code: {e}")
        return False, str(e)

def bulk_insert_cost_codes(dataframe_payload):
    try:
        if dataframe_payload.empty:
            return False, "Empty dataframe provided."
        
        # Ensure correct column names
        if 'code' not in dataframe_payload.columns or 'description' not in dataframe_payload.columns:
            return False, "CSV must contain 'code' and 'description' columns."
        
        # Drop duplicates in payload
        df_clean = dataframe_payload.drop_duplicates(subset=['code'])
        
        # Get existing codes
        existing_res = supabase.table('cost_codes').select('code_number').execute()
        existing_codes = set([r['code_number'] for r in existing_res.data]) if existing_res.data else set()
        
        # Filter new codes
        new_records = []
        for _, row in df_clean.iterrows():
            if str(row['code']).strip() not in existing_codes:
                new_records.append({
                    "code_number": str(row['code']).strip(),
                    "description": str(row['description']).strip()
                })
        
        if new_records:
            supabase.table('cost_codes').insert(new_records).execute()
            
        return True, f"Successfully imported {len(new_records)} new cost codes."
    except Exception as e:
        print(f"Error bulk inserting cost codes: {e}")
        return False, str(e)

def get_cost_codes(project_id=None):
    try:
        if project_id:
            # Check if project has specific cost codes mapped
            mapped_res = supabase.table('project_cost_codes').select('cost_code_id').eq('project_id', project_id).execute()
            if mapped_res.data:
                cc_ids = [r['cost_code_id'] for r in mapped_res.data]
                response = supabase.table('cost_codes').select('id, code_number, description').in_('id', cc_ids).execute()
            else:
                # Fallback to all cost codes
                response = supabase.table('cost_codes').select('id, code_number, description').execute()
        else:
            response = supabase.table('cost_codes').select('id, code_number, description').execute()
            
        df = pd.DataFrame(response.data) if response.data else pd.DataFrame(columns=['id', 'code_number', 'description'])
        if not df.empty:
            df['display_name'] = df['code_number'] + ' ' + df['description']
        return df
    except Exception as e:
        print(f"Error fetching cost codes: {e}")
        return pd.DataFrame(columns=['id', 'code_number', 'description', 'display_name'])

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

def log_equipment(date, project_id, employee_id, equipment_id, cost_code_id, hours_used, start_meter=None, end_meter=None, calculated_runtime=None):
    data = {
        "date": str(date),
        "project_id": project_id,
        "employee_id": employee_id,
        "equipment_id": equipment_id,
        "cost_code_id": cost_code_id,
        "hours_used": hours_used
    }
    if start_meter is not None:
        data["start_meter"] = start_meter
    if end_meter is not None:
        data["end_meter"] = end_meter
    if calculated_runtime is not None:
        data["calculated_runtime"] = calculated_runtime
        
    supabase.table('equipment_logs').insert(data).execute()

def get_latest_equipment_meter(equipment_id):
    try:
        response = supabase.table('equipment_logs').select('end_meter').eq('equipment_id', equipment_id).order('date', desc=True).order('id', desc=True).limit(1).execute()
        if response.data and response.data[0].get('end_meter') is not None:
            return response.data[0]['end_meter']
    except Exception as e:
        print(f"Error fetching latest equipment meter: {e}")
    return 0.0

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
    projs = pd.DataFrame(supabase.table('projects').select('id, job_number, project_name').execute().data)
    emps = pd.DataFrame(supabase.table('employees').select('id, first_name, last_name').execute().data)
    eqs = pd.DataFrame(supabase.table('equipment').select('id, unit_number, make_model').execute().data)
    ccs = pd.DataFrame(supabase.table('cost_codes').select('id, code_number, description').execute().data)
    
    # Merge
    df = logs_df.merge(projs, left_on='project_id', right_on='id', suffixes=('', '_p'))
    df = df.merge(emps, left_on='employee_id', right_on='id', suffixes=('', '_e'))
    df = df.merge(eqs, left_on='equipment_id', right_on='id', suffixes=('', '_eq'))
    df = df.merge(ccs, left_on='cost_code_id', right_on='id', suffixes=('', '_c'))
    
    df['Project'] = df['job_number'].fillna('') + ' ' + df['project_name']
    df['Project'] = df['Project'].str.strip()
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
    if not res.data:
        return pd.DataFrame(columns=['Date', 'Project', 'Worker', 'Start Time', 'End Time', 'Cost Code', 'Status', 'Total Labor Hours', 'Total Labor Cost ($)', 'Description'])
        
    df = pd.DataFrame(res.data)
    projs = pd.DataFrame(supabase.table('projects').select('job_number, project_name').execute().data)
    df = df.merge(projs, left_on='Project', right_on='project_name', how='left')
    df['Project'] = df['job_number'].fillna('') + ' ' + df['Project']
    df['Project'] = df['Project'].str.strip()
    df = df.drop(columns=['job_number', 'project_name'])
    return df

def get_equipment_summary():
    # No view was created, fetch and join in pandas
    eq_logs = supabase.table('equipment_logs').select('*').execute()
    if not eq_logs.data:
        return pd.DataFrame(columns=['Date', 'Project', 'Equipment Asset', 'Cost Code', 'Status', 'Total Equipment Hours', 'Total Equipment Cost ($)'])
        
    logs_df = pd.DataFrame(eq_logs.data)
    projs = pd.DataFrame(supabase.table('projects').select('id, job_number, project_name').execute().data)
    eqs = pd.DataFrame(supabase.table('equipment').select('id, unit_number, make_model, hourly_rate').execute().data)
    ccs = pd.DataFrame(supabase.table('cost_codes').select('id, code_number, description').execute().data)
    
    df = logs_df.merge(projs, left_on='project_id', right_on='id', suffixes=('', '_p'))
    df = df.merge(eqs, left_on='equipment_id', right_on='id', suffixes=('', '_eq'))
    df = df.merge(ccs, left_on='cost_code_id', right_on='id', suffixes=('', '_c'))
    
    df['Project'] = df['job_number'].fillna('') + ' ' + df['project_name']
    df['Project'] = df['Project'].str.strip()
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
    projs = pd.DataFrame(supabase.table('projects').select('id, job_number, project_name').execute().data)
    df = df.merge(projs, left_on='project_id', right_on='id', suffixes=('', '_p'))
    df['Project'] = df['job_number'].fillna('') + ' ' + df['project_name']
    df['Project'] = df['Project'].str.strip()
    return df

def get_employee_timecard_summary(employee_id, start_date, end_date):
    try:
        res = supabase.table('labor_logs').select('hours_worked, status').eq('employee_id', employee_id).gte('date', start_date).lte('date', end_date).execute()
        df = pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=['hours_worked', 'status'])
        if df.empty:
            return {"Approved": 0.0, "Pending": 0.0}
        
        summary = df.groupby('status')['hours_worked'].sum().to_dict()
        return {
            "Approved": summary.get('Approved', 0.0),
            "Pending": summary.get('Pending', 0.0)
        }
    except Exception as e:
        print(f"Error fetching timecard summary: {e}")
        return {"Approved": 0.0, "Pending": 0.0}


def get_latest_user_logs(employee_id):
    try:
        # Fetch the latest labor log for the user
        labor_res = supabase.table('labor_logs').select('project_id, cost_code_id').eq('employee_id', employee_id).order('date', desc=True).order('id', desc=True).limit(1).execute()
        
        # Fetch the latest equipment log for the user
        equipment_res = supabase.table('equipment_logs').select('equipment_id').eq('employee_id', employee_id).order('date', desc=True).order('id', desc=True).limit(1).execute()
        
        latest_project_id = None
        latest_cost_code_id = None
        latest_equipment_id = None
        
        if labor_res.data:
            latest_project_id = labor_res.data[0]['project_id']
            latest_cost_code_id = labor_res.data[0]['cost_code_id']
            
        if equipment_res.data:
            latest_equipment_id = equipment_res.data[0]['equipment_id']
            # If labor_res didn't have a project_id, but equipment_res does, we could grab it, but equipment_logs has project_id as well.
            # Let's fetch project_id from equipment logs if we didn't get it from labor logs
            if not latest_project_id:
                # fetch project_id for equipment log too to be safe
                eq_proj_res = supabase.table('equipment_logs').select('project_id').eq('employee_id', employee_id).order('date', desc=True).order('id', desc=True).limit(1).execute()
                if eq_proj_res.data:
                    latest_project_id = eq_proj_res.data[0]['project_id']

        return {
            "project_id": latest_project_id,
            "cost_code_id": latest_cost_code_id,
            "equipment_id": latest_equipment_id
        }
    except Exception as e:
        print(f"Error fetching latest logs: {e}")
        return {
            "project_id": None,
            "cost_code_id": None,
            "equipment_id": None
        }

def get_integration_settings():
    try:
        res = supabase.table('integration_settings').select('*').limit(1).execute()
        if res.data:
            return res.data[0]
        return None
    except Exception as e:
        print(f"Error fetching integration settings: {e}")
        return None

def save_integration_settings(procore_client_id, procore_client_secret, vision_ai_key, openai_api_key=""):
    try:
        existing = get_integration_settings()
        data = {
            "procore_client_id": procore_client_id,
            "procore_client_secret": procore_client_secret,
            "vision_ai_key": vision_ai_key,
            "openai_api_key": openai_api_key
        }
        if existing:
            supabase.table('integration_settings').update(data).eq('id', existing['id']).execute()
        else:
            supabase.table('integration_settings').insert(data).execute()
        return True
    except Exception as e:
        return False

def upload_company_logo(file_bytes):
    try:
        supabase.storage.from_("company-assets").upload("logo.png", file_bytes, file_options={"upsert": "true", "content-type": "image/png"})
        return True
    except Exception as e:
        print(f"Error uploading logo: {e}")
        return False

def get_company_logo():
    try:
        return supabase.storage.from_("company-assets").download("logo.png")
    except Exception as e:
        return None

def log_material(project_id, user_id, cost_code_id, date, log_type, supplier, material_description, quantity, unit, scanned_ticket_url=None):
    try:
        supabase.table('material_logs').insert({
            "project_id": project_id,
            "user_id": user_id,
            "cost_code_id": cost_code_id,
            "date": str(date),
            "log_type": log_type,
            "supplier": supplier,
            "material_description": material_description,
            "quantity": quantity,
            "unit": unit,
            "scanned_ticket_url": scanned_ticket_url
        }).execute()
        return True
    except Exception as e:
        print(f"Error logging material: {e}")
        return False

def get_daily_material_logs(project_id, target_date):
    try:
        # We assume there's a cost_codes relation if cost_code_id is not null
        res = supabase.table('material_logs').select('*, cost_codes(code_number, description), employees!user_id(first_name, last_name)').eq('project_id', project_id).eq('date', str(target_date)).execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except Exception as e:
        print(f"Error fetching daily material logs: {e}")
        return pd.DataFrame()

def log_subcontractor(project_id, user_id, cost_code_id, date, company_name, scope_of_work, hours_worked, comments="", ticket_number=None, scanned_ticket_url=None):
    try:
        supabase.table('subcontractor_logs').insert({
            "project_id": project_id,
            "user_id": user_id,
            "cost_code_id": cost_code_id,
            "date": str(date),
            "company_name": company_name,
            "scope_of_work": scope_of_work,
            "hours_worked": hours_worked,
            "comments": comments,
            "ticket_number": ticket_number,
            "scanned_ticket_url": scanned_ticket_url
        }).execute()
        return True
    except Exception as e:
        print(f"Error logging subcontractor: {e}")
        return False

def get_daily_subcontractor_logs(project_id, target_date):
    try:
        res = supabase.table('subcontractor_logs').select('*, cost_codes(code_number, description), employees!user_id(first_name, last_name)').eq('project_id', project_id).eq('date', str(target_date)).execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except Exception as e:
        print(f"Error fetching daily subcontractor logs: {e}")
        return pd.DataFrame()

def upload_ticket_image(file_bytes, filename):
    try:
        # Generate a unique path to avoid collisions
        unique_filename = f"{secrets.token_hex(8)}_{filename}"
        res = supabase.storage.from_("tickets").upload(unique_filename, file_bytes, file_options={"upsert": "false"})
        # Get public URL
        public_url = supabase.storage.from_("tickets").get_public_url(unique_filename)
        return public_url
    except Exception as e:
        print(f"Error uploading ticket: {e}")
        return None


def get_all_material_logs():
    try:
        res = supabase.table('material_logs').select('*, projects(job_number, project_name), cost_codes(code_number, description), employees!user_id(first_name, last_name)').execute()
        df = pd.DataFrame(res.data) if res.data else pd.DataFrame()
        if not df.empty:
            # Flatten relations
            df['Project'] = df['projects'].apply(lambda x: f"{x.get('job_number','')} {x.get('project_name','')}").str.strip() if 'projects' in df else ''
            df['Cost Code'] = df['cost_codes'].apply(lambda x: f"{x.get('code_number','')} {x.get('description','')}" if x else '') if 'cost_codes' in df else ''
            df['Logged By'] = df['employees'].apply(lambda x: f"{x.get('first_name','')} {x.get('last_name','')}" if x else '') if 'employees' in df else ''
            df['Date'] = df['date']
            df['Log Type'] = df['log_type']
            df['Supplier'] = df['supplier']
            df['Description'] = df['material_description']
            df['Qty'] = df['quantity'].astype(str) + ' ' + df['unit'].astype(str)
            df['Ticket URL'] = df['scanned_ticket_url']
            return df[['Date', 'Project', 'Logged By', 'Cost Code', 'Log Type', 'Supplier', 'Description', 'Qty', 'Ticket URL']].sort_values('Date', ascending=False)
        return pd.DataFrame()
    except Exception as e:
        print(f"Error fetching all material logs: {e}")
        return pd.DataFrame()

def get_all_subcontractor_logs():
    try:
        res = supabase.table('subcontractor_logs').select('*, projects(job_number, project_name), cost_codes(code_number, description), employees!user_id(first_name, last_name)').execute()
        df = pd.DataFrame(res.data) if res.data else pd.DataFrame()
        if not df.empty:
            df['Project'] = df['projects'].apply(lambda x: f"{x.get('job_number','')} {x.get('project_name','')}").str.strip() if 'projects' in df else ''
            df['Cost Code'] = df['cost_codes'].apply(lambda x: f"{x.get('code_number','')} {x.get('description','')}" if x else '') if 'cost_codes' in df else ''
            df['Logged By'] = df['employees'].apply(lambda x: f"{x.get('first_name','')} {x.get('last_name','')}" if x else '') if 'employees' in df else ''
            df['Date'] = df['date']
            df['Company'] = df['company_name']
            df['Ticket #'] = df['ticket_number']
            df['Scope'] = df['scope_of_work']
            df['Hours'] = df['hours_worked']
            df['Comments'] = df['comments']
            df['Ticket URL'] = df['scanned_ticket_url']
            return df[['Date', 'Project', 'Logged By', 'Cost Code', 'Company', 'Ticket #', 'Scope', 'Hours', 'Comments', 'Ticket URL']].sort_values('Date', ascending=False)
        return pd.DataFrame()
    except Exception as e:
        print(f"Error fetching all subcontractor logs: {e}")
        return pd.DataFrame()

def get_daily_report_data(project_id, target_date):
    try:
        labor_res = supabase.table('labor_logs').select('*, employees(first_name, last_name, role), cost_codes(code, description)').eq('project_id', project_id).eq('date', str(target_date)).execute()
        labor_data = labor_res.data if labor_res.data else []

        eq_res = supabase.table('equipment_logs').select('*, equipment(make, model, unit_number), cost_codes(code, description)').eq('project_id', project_id).eq('date', str(target_date)).execute()
        eq_data = eq_res.data if eq_res.data else []
        
        mat_res = supabase.table('material_logs').select('*, cost_codes(code, description)').eq('project_id', project_id).eq('date', str(target_date)).execute()
        mat_data = mat_res.data if mat_res.data else []

        sub_res = supabase.table('subcontractor_logs').select('*, cost_codes(code, description)').eq('project_id', project_id).eq('date', str(target_date)).execute()
        sub_data = sub_res.data if sub_res.data else []

        proj_res = supabase.table('projects').select('*').eq('id', project_id).execute()
        project_data = proj_res.data[0] if proj_res.data else None

        return {
            "project": project_data,
            "labor_logs": labor_data,
            "equipment_logs": eq_data,
            "material_logs": mat_data,
            "subcontractor_logs": sub_data
        }
    except Exception as e:
        print(f"Error fetching daily report data: {e}")
        return None

def send_password_reset_email(email):
    if supabase is None:
        return f"Database client not initialized. Error: {supabase_init_error}"
    try:
        # Note: the redirect_to URL should match your deployed app URL.
        supabase.auth.reset_password_for_email(
            email, 
            options={"redirect_to": "https://cost-code-tracker-94816924591.us-central1.run.app/"}
        )
        return True
    except Exception as e:
        return str(e)
