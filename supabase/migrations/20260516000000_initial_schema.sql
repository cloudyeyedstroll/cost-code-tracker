-- Initial Database Schema & Seed Data for Supabase

CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    project_name TEXT NOT NULL,
    location TEXT NOT NULL,
    procore_id TEXT
);

CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    -- We removed password and invite_token as Supabase Auth handles that
    account_status TEXT DEFAULT 'Pending',
    procore_id TEXT,
    hourly_rate REAL DEFAULT 0.0,
    role TEXT DEFAULT 'Crew',
    auth_id UUID -- Links to auth.users in Supabase
);

CREATE TABLE equipment (
    id SERIAL PRIMARY KEY,
    unit_number TEXT NOT NULL,
    make_model TEXT NOT NULL,
    procore_id TEXT,
    hourly_rate REAL DEFAULT 0.0
);

CREATE TABLE cost_codes (
    id SERIAL PRIMARY KEY,
    code_number TEXT NOT NULL,
    description TEXT NOT NULL,
    procore_id TEXT
);

CREATE TABLE labor_logs (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    employee_id INTEGER NOT NULL REFERENCES employees(id),
    cost_code_id INTEGER NOT NULL REFERENCES cost_codes(id),
    start_time TEXT,
    end_time TEXT,
    hours_worked REAL NOT NULL,
    work_description TEXT,
    status TEXT DEFAULT 'Pending'
);

CREATE TABLE equipment_logs (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    employee_id INTEGER NOT NULL REFERENCES employees(id),
    equipment_id INTEGER NOT NULL REFERENCES equipment(id),
    cost_code_id INTEGER NOT NULL REFERENCES cost_codes(id),
    hours_used REAL NOT NULL,
    status TEXT DEFAULT 'Pending'
);

-- Dashboard Views
CREATE VIEW pending_labor_logs_view AS
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
ORDER BY l.date DESC;

CREATE VIEW labor_summary_view AS
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
ORDER BY l.date DESC;

-- Seed Data
INSERT INTO projects (project_name, location) VALUES 
('208th Street Upgrades', 'Langley, BC'),
('Storm Line Replacement', 'Port of Vancouver');

INSERT INTO equipment (unit_number, make_model, hourly_rate) VALUES 
('EX-402', 'Caterpillar 320 Hydraulic Excavator', 150.00),
('DZ-115', 'John Deere 850L Crawler Dozer', 130.00),
('LD-08', 'Komatsu WA380 Wheel Loader', 110.00);

INSERT INTO cost_codes (code_number, description) VALUES 
('02-300', 'Earthwork & Mass Excavation'),
('02-450', 'Storm Sewer Installation'),
('02-500', 'Watermain Utilities'),
('01-520', 'Traffic Control Services (LCT)');

INSERT INTO employees (first_name, last_name, email, account_status, hourly_rate, role) VALUES 
('Allen', 'Goodman', 'allen@company.com', 'Active', 45.00, 'Admin'),
('Dave', 'Miller', 'dave@company.com', 'Active', 40.00, 'Crew'),
('Chris', 'Evans', 'chris@company.com', 'Active', 35.00, 'Foreman');
