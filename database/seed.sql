-- ==========================================
-- Approved Assessment Targets
-- ==========================================

INSERT INTO targets (name, ip_address, location, description)
VALUES
    ('Oregon Test Server', '192.0.2.10', 'Oregon',
        'Approved testing target in Oregon'),

    ('Virginia Test Server', '192.0.2.20', 'Virginia',
        'Approved testing target in Virginia'),

    ('Colorado Test Server', '192.0.2.30', 'Colorado',
        'Approved testing target in Colorado');


-- ==========================================
-- Assessment Agents
-- ==========================================

INSERT INTO agents (name, location)
VALUES
    ('Oregon Worker', 'Oregon'),
    ('Virginia Worker', 'Virginia'),
    ('Colorado Worker', 'Colorado');
