-- ==========================================
-- Targets: Table storing information about the targets to be assessed.
-- ==========================================

CREATE TABLE targets (
    target_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    ip_address INET NOT NULL UNIQUE,
    location VARCHAR(100),
    description TEXT,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);


-- ==========================================
-- Assessment Agents: Table storing information about the agents performing assessments.
-- ==========================================

CREATE TABLE agents (
    agent_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(100),
    enabled BOOLEAN DEFAULT TRUE,
    last_seen_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);


-- ==========================================
-- Assessments
-- ==========================================

CREATE TABLE assessments (
    assessment_id SERIAL PRIMARY KEY,
    target_id INTEGER NOT NULL REFERENCES targets(target_id),
    agent_id INTEGER REFERENCES agents(agent_id),
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN (
            'pending',
            'running',
            'completed',
            'failed'
        )),

    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    error_message TEXT
);


-- ==========================================
-- Assessment Ports: The ports an assessment is intended to test.
-- ==========================================

CREATE TABLE assessment_ports (
    assessment_id INTEGER NOT NULL REFERENCES assessments(assessment_id) 
        ON DELETE CASCADE,

    port INTEGER NOT NULL CHECK (port BETWEEN 1 AND 65535),
    PRIMARY KEY (assessment_id, port)
);


-- ==========================================
-- Assessment Tests: The types of tests an assessment is intended to perform.
-- ==========================================

CREATE TABLE assessment_tests (
    assessment_id INTEGER NOT NULL
        REFERENCES assessments(assessment_id)
        ON DELETE CASCADE,

    test_type VARCHAR(30) NOT NULL
        CHECK (test_type IN (
            'tcp_connectivity',
            'latency',
            'throughput',
            'packet_loss'
        )),

    PRIMARY KEY (assessment_id, test_type)
);


-- ==========================================
-- Assessment Results: The results of the tests performed during an assessment.
-- ==========================================

CREATE TABLE assessment_results (
    result_id SERIAL PRIMARY KEY,
    assessment_id INTEGER NOT NULL,
    port INTEGER,
    test_type VARCHAR(30) NOT NULL,
    metric_name VARCHAR(50) NOT NULL,
    metric_value NUMERIC(15, 4),
    unit VARCHAR(20),
    details JSONB,
    measured_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (assessment_id, test_type)
        REFERENCES assessment_tests(assessment_id, test_type),

    FOREIGN KEY (assessment_id, port)
        REFERENCES assessment_ports(assessment_id, port)
);


-- ==========================================
-- Indexes
-- ==========================================

CREATE INDEX idx_assessments_target
    ON assessments(target_id);

CREATE INDEX idx_assessments_agent
    ON assessments(agent_id);

CREATE INDEX idx_assessments_status
    ON assessments(status);

CREATE INDEX idx_results_assessment
    ON assessment_results(assessment_id);

CREATE INDEX idx_results_measured_at
    ON assessment_results(measured_at);
