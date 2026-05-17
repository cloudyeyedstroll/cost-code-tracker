import sqlite3
import pandas as pd
import os

DB_NAME = 'job_costing_v7.db'

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create projects table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_name TEXT NOT NULL,
        location TEXT NOT NULL,
        procore_id TEXT
    )
    ''')
    
    # Create employees table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT,
        invite_token TEXT,
        account_status TEXT DEFAULT 'Pending',
        procore_id TEXT,
        hourly_rate REAL,
        role TEXT DEFAULT 'Crew'
    )
    ''')
    
    # Create equipment table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS equipment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        unit_number TEXT NOT NULL,
        make_model TEXT NOT NULL,
        procore_id TEXT,
        hourly_rate REAL
    )
    ''')
    
    # Create cost_codes table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cost_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code_number TEXT NOT NULL,
        description TEXT NOT NULL,
        procore_id TEXT
    )
    ''')
    
    # Create labor_logs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS labor_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        project_id INTEGER NOT NULL,
        employee_id INTEGER NOT NULL,
        cost_code_id INTEGER NOT NULL,
        start_time TEXT,
        end_time TEXT,
        hours_worked REAL NOT NULL,
        work_description TEXT,
        status TEXT DEFAULT 'Pending',
        FOREIGN KEY (project_id) REFERENCES projects(id),
        FOREIGN KEY (employee_id) REFERENCES employees(id),
        FOREIGN KEY (cost_code_id) REFERENCES cost_codes(id)
    )
    ''')
    
    # Create equipment_logs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS equipment_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        project_id INTEGER NOT NULL,
        employee_id INTEGER NOT NULL,
        equipment_id INTEGER NOT NULL,
        cost_code_id INTEGER NOT NULL,
        hours_used REAL NOT NULL,
        status TEXT DEFAULT 'Pending',
        FOREIGN KEY (project_id) REFERENCES projects(id),
        FOREIGN KEY (employee_id) REFERENCES employees(id),
        FOREIGN KEY (equipment_id) REFERENCES equipment(id),
        FOREIGN KEY (cost_code_id) REFERENCES cost_codes(id)
    )
    ''')
    
    conn.commit()
    conn.close()

def seed_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if we already seeded
    cursor.execute('SELECT COUNT(*) FROM projects')
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    # Insert projects
    cursor.executemany('''
    INSERT INTO projects (project_name, location, procore_id)
    VALUES (?, ?, ?)
    ''', [
        ('208th Street Upgrades', 'Langley, BC', None),
        ('Storm Line Replacement', 'Port of Vancouver', None)
    ])
    
    # Insert employees
    cursor.executemany('''
    INSERT INTO employees (first_name, last_name, email, password, account_status, procore_id, hourly_rate, role)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', [
        ('Allen', 'Goodman', 'allen@company.com', 'password123', 'Active', None, 45.00, 'Admin'),
        ('Dave', 'Miller', 'dave@company.com', 'password123', 'Active', None, 40.00, 'Crew'),
        ('Chris', 'Evans', 'chris@company.com', 'password123', 'Active', None, 35.00, 'Foreman')
    ])
    
    # Insert equipment
    cursor.executemany('''
    INSERT INTO equipment (unit_number, make_model, procore_id, hourly_rate)
    VALUES (?, ?, ?, ?)
    ''', [
        ('EX-402', 'Caterpillar 320 Hydraulic Excavator', None, 150.00),
        ('DZ-115', 'John Deere 850L Crawler Dozer', None, 130.00),
        ('LD-08', 'Komatsu WA380 Wheel Loader', None, 110.00)
    ])
    
    # Insert cost codes
    cursor.executemany('''
    INSERT INTO cost_codes (code_number, description, procore_id)
    VALUES (?, ?, ?)
    ''', [
        ('02-300', 'Earthwork & Mass Excavation', None),
        ('02-450', 'Storm Sewer Installation', None),
        ('02-500', 'Watermain Utilities', None),
        ('01-520', 'Traffic Control Services (LCT)', None)
    ])
    
    conn.commit()
    conn.close()

# Helper queries for UI
def get_projects():
    conn = get_connection()
    df = pd.read_sql_query('SELECT id, project_name FROM projects', conn)
    conn.close()
    return df

def get_employees():
    conn = get_connection()
    df = pd.read_sql_query('SELECT id, first_name, last_name, role FROM employees', conn)
    df['full_name'] = df['first_name'] + ' ' + df['last_name']
    conn.close()
    return df

def get_equipment():
    conn = get_connection()
    df = pd.read_sql_query('SELECT id, unit_number, make_model FROM equipment', conn)
    df['display_name'] = df['unit_number'] + ' - ' + df['make_model']
    conn.close()
    return df

def get_cost_codes():
    conn = get_connection()
    df = pd.read_sql_query('SELECT id, code_number, description FROM cost_codes', conn)
    df['display_name'] = df['code_number'] + ' ' + df['description']
    conn.close()
    return df

def log_labor(date, project_id, employee_id, cost_code_id, hours_worked, work_description="", start_time="", end_time=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO labor_logs (date, project_id, employee_id, cost_code_id, start_time, end_time, hours_worked, work_description)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (date, project_id, employee_id, cost_code_id, start_time, end_time, hours_worked, work_description))
    conn.commit()
    conn.close()

def log_equipment(date, project_id, employee_id, equipment_id, cost_code_id, hours_used):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO equipment_logs (date, project_id, employee_id, equipment_id, cost_code_id, hours_used)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (date, project_id, employee_id, equipment_id, cost_code_id, hours_used))
    conn.commit()
    conn.close()

def get_employee_role(employee_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT role FROM employees WHERE id = ?', (employee_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 'Crew'

def update_employee_permissions(employee_id, new_role):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE employees
    SET role = ?
    WHERE id = ?
    ''', (new_role, employee_id))
    conn.commit()
    conn.close()

def create_employee_invite(first_name, last_name, email, role, token):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO employees (first_name, last_name, email, invite_token, account_status, procore_id, hourly_rate, role)
    VALUES (?, ?, ?, ?, 'Pending', NULL, 0.0, ?)
    ''', (first_name, last_name, email, token, role))
    conn.commit()
    conn.close()

def get_employee_by_token(token):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, first_name, last_name, email, account_status FROM employees WHERE invite_token = ?', (token,))
    res = cursor.fetchone()
    conn.close()
    if res:
        return {"id": res[0], "first_name": res[1], "last_name": res[2], "email": res[3], "account_status": res[4]}
    return None

def activate_employee_account(employee_id, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE employees
    SET password = ?, invite_token = NULL, account_status = 'Active'
    WHERE id = ?
    ''', (password, employee_id))
    conn.commit()
    conn.close()

def delete_employee(employee_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check for existing logs to maintain data integrity safely
    cursor.execute("SELECT COUNT(*) FROM labor_logs WHERE employee_id = ?", (employee_id,))
    labor_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM equipment_logs WHERE employee_id = ?", (employee_id,))
    eq_count = cursor.fetchone()[0]
    
    if labor_count > 0 or eq_count > 0:
        conn.close()
        return False, "Cannot delete employee: they have existing labor or equipment logs."
        
    cursor.execute('DELETE FROM employees WHERE id = ?', (employee_id,))
    conn.commit()
    conn.close()
    return True, "Employee permanently deleted."

def get_pending_labor_logs():
    conn = get_connection()
    query = '''
    SELECT 
        l.id as log_id,
        l.date as "Date",
        p.id as project_id,
        p.project_name as "Project",
        emp.first_name || ' ' || emp.last_name as "Worker",
        l.start_time as "Start Time",
        l.end_time as "End Time",
        cc.code_number || ' ' || cc.description as "Cost Code",
        l.hours_worked as "Hours",
        l.work_description as "Description"
    FROM labor_logs l
    JOIN projects p ON l.project_id = p.id
    JOIN employees emp ON l.employee_id = emp.id
    JOIN cost_codes cc ON l.cost_code_id = cc.id
    WHERE l.status = 'Pending'
    ORDER BY l.date DESC
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_pending_equipment_logs():
    conn = get_connection()
    query = '''
    SELECT 
        e.id as log_id,
        e.date as "Date",
        p.id as project_id,
        p.project_name as "Project",
        emp.first_name || ' ' || emp.last_name as "Logged By",
        eq.unit_number || ' - ' || eq.make_model as "Equipment Asset",
        cc.code_number || ' ' || cc.description as "Cost Code",
        e.hours_used as "Hours"
    FROM equipment_logs e
    JOIN projects p ON e.project_id = p.id
    JOIN employees emp ON e.employee_id = emp.id
    JOIN equipment eq ON e.equipment_id = eq.id
    JOIN cost_codes cc ON e.cost_code_id = cc.id
    WHERE e.status = 'Pending'
    ORDER BY e.date DESC
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def approve_labor_log(log_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE labor_logs SET status = 'Approved' WHERE id = ?", (log_id,))
    conn.commit()
    conn.close()

def approve_equipment_log(log_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE equipment_logs SET status = 'Approved' WHERE id = ?", (log_id,))
    conn.commit()
    conn.close()

def approve_all_pending(project_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE labor_logs SET status = 'Approved' WHERE project_id = ? AND status = 'Pending'", (project_id,))
    cursor.execute("UPDATE equipment_logs SET status = 'Approved' WHERE project_id = ? AND status = 'Pending'", (project_id,))
    conn.commit()
    conn.close()

# Summary queries for Dashboard
def get_labor_summary():
    conn = get_connection()
    query = '''
    SELECT 
        l.date as "Date",
        p.project_name as "Project",
        emp.first_name || ' ' || emp.last_name as "Worker",
        l.start_time as "Start Time",
        l.end_time as "End Time",
        cc.code_number || ' ' || cc.description as "Cost Code",
        l.status as "Status",
        SUM(l.hours_worked) as "Total Labor Hours",
        SUM(l.hours_worked * emp.hourly_rate) as "Total Labor Cost ($)",
        l.work_description as "Description"
    FROM labor_logs l
    JOIN projects p ON l.project_id = p.id
    JOIN cost_codes cc ON l.cost_code_id = cc.id
    JOIN employees emp ON l.employee_id = emp.id
    GROUP BY l.date, p.project_name, emp.id, l.start_time, l.end_time, cc.code_number, cc.description, l.status, l.work_description
    ORDER BY l.date DESC
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_equipment_summary():
    conn = get_connection()
    query = '''
    SELECT 
        e.date as "Date",
        p.project_name as "Project",
        eq.unit_number || ' - ' || eq.make_model as "Equipment Asset",
        cc.code_number || ' ' || cc.description as "Cost Code",
        e.status as "Status",
        SUM(e.hours_used) as "Total Equipment Hours",
        SUM(e.hours_used * eq.hourly_rate) as "Total Equipment Cost ($)"
    FROM equipment_logs e
    JOIN projects p ON e.project_id = p.id
    JOIN equipment eq ON e.equipment_id = eq.id
    JOIN cost_codes cc ON e.cost_code_id = cc.id
    GROUP BY e.date, p.project_name, eq.unit_number, eq.make_model, cc.code_number, cc.description, e.status
    ORDER BY e.date DESC
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def verify_employee_login(email, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT id, first_name, last_name, role 
    FROM employees 
    WHERE email = ? AND password = ? AND account_status = 'Active'
    ''', (email, password))
    res = cursor.fetchone()
    conn.close()
    if res:
        return {"id": res[0], "first_name": res[1], "last_name": res[2], "role": res[3], "full_name": f"{res[1]} {res[2]}"}
    return None

# Helper to check if DB exists and initialize it
def setup():
    if not os.path.exists(DB_NAME):
        init_db()
        seed_db()
