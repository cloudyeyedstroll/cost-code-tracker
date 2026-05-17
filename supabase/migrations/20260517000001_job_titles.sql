CREATE TABLE IF NOT EXISTS job_titles (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title_name TEXT UNIQUE NOT NULL,
    permission_tier TEXT NOT NULL CHECK (permission_tier IN ('Admin', 'Foreman', 'Crew'))
);

-- Seed baseline roles including existing raw tiers to maintain backwards compatibility 
-- with any existing employees in the database.
INSERT INTO job_titles (title_name, permission_tier) VALUES
('Superintendent', 'Admin'),
('President', 'Admin'),
('Civil Coordinator', 'Admin'),
('Estimator', 'Admin'),
('Controller', 'Admin'),
('Operator', 'Crew'),
('Grademan', 'Crew'),
('Pipelayer', 'Crew'),
('Laborer', 'Crew'),
('Admin', 'Admin'),
('Foreman', 'Foreman'),
('Crew', 'Crew')
ON CONFLICT (title_name) DO NOTHING;
