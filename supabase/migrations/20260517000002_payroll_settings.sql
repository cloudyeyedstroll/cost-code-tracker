-- supabase/migrations/20260517000002_payroll_settings.sql
CREATE TABLE IF NOT EXISTS payroll_settings (
    id INT PRIMARY KEY,
    current_period_start DATE NOT NULL,
    current_period_end DATE NOT NULL
);
