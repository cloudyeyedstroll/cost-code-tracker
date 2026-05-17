-- Migration to add Force Accounts and update related tables

-- Add invite_token to employees if they want to use it
ALTER TABLE employees ADD COLUMN IF NOT EXISTS invite_token TEXT;

-- Create force_accounts table
CREATE TABLE IF NOT EXISTS force_accounts (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    date DATE DEFAULT now(),
    project_id INTEGER NOT NULL REFERENCES projects(id),
    client_representative TEXT NOT NULL,
    signature_data TEXT NOT NULL
);

-- Alter labor_logs to add force_account_id
ALTER TABLE labor_logs ADD COLUMN IF NOT EXISTS force_account_id BIGINT REFERENCES force_accounts(id) DEFAULT NULL;

-- Alter equipment_logs to add force_account_id
ALTER TABLE equipment_logs ADD COLUMN IF NOT EXISTS force_account_id BIGINT REFERENCES force_accounts(id) DEFAULT NULL;
