import pandas as pd
import os
from supabase import create_client, Client
from dotenv import load_dotenv
import secrets

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

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
    # For Supabase Auth, we generate a temp password (which acts as our invite token)
    temp_password = token if token else secrets.token_urlsafe(16)
    
    # Create the user in Supabase Auth
    try:
        auth_response = supabase.auth.admin.create_user({
            "email": email,
            "password": temp_password,
            "email_confirm": True
        })
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
        return temp_password
    except Exception as e:
        print(f"Error creating employee: {e}")
        return None

def get_employee_by_token(email):
    # We repurpose this to fetch by email during activation
    res = supabase.table('employees').select('id, first_name, last_name, email, account_status').eq('email', email).execute()
    return res.data[0] if res.data else None

def activate_employee_account(employee_email, temp_password, new_password):
    # Log them in with the temp password to get a session
    try:
        res = supabase.auth.sign_in_with_password({"email": employee_email, "password": temp_password})
        if res.session:
            # Now we can update their password securely
            supabase.auth.update_user({"password": new_password})
            # Update their status in the public.employees table
            supabase.table('employees').update({"account_status": "Active"}).eq('email', employee_email).execute()
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
    try:
        # Authenticate with Supabase Auth
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if res.session:
            # Fetch user details from public.employees
            emp_res = supabase.table('employees').select('id, first_name, last_name, role, account_status').eq('email', email).execute()
            if emp_res.data and emp_res.data[0]['account_status'] == 'Active':
                emp = emp_res.data[0]
                return {
                    "id": emp['id'], 
                    "first_name": emp['first_name'], 
                    "last_name": emp['last_name'], 
                    "role": emp['role'], 
                    "full_name": f"{emp['first_name']} {emp['last_name']}"
                }
    except Exception as e:
        print(f"Login error: {e}")
    return None

