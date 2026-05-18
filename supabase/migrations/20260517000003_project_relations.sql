-- supabase/migrations/20260517000003_project_relations.sql
-- Create mapping tables for Many-to-Many relationships between Projects and Scope (Cost Codes & Equipment)

CREATE TABLE IF NOT EXISTS project_cost_codes (
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    cost_code_id INTEGER REFERENCES cost_codes(id) ON DELETE CASCADE,
    PRIMARY KEY (project_id, cost_code_id)
);

CREATE TABLE IF NOT EXISTS project_equipment (
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    equipment_id INTEGER REFERENCES equipment(id) ON DELETE CASCADE,
    PRIMARY KEY (project_id, equipment_id)
);
