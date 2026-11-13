-- ==========================================
-- Approved Assessment Targets
-- ==========================================

INSERT INTO targets (name, ip_address, location, description)
VALUES
    ('My Test Server', '127.0.0.1', 'Local',
        'My own server used for testing');


-- ==========================================
-- Assessment Agents
-- ==========================================

INSERT INTO agents (name, location)
VALUES
    ('Oregon Worker', 'Oregon'),
    ('Virginia Worker', 'Virginia'),
    ('Colorado Worker', 'Colorado');
