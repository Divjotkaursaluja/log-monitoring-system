CREATE TABLE IF NOT EXISTS agents (
    agent_id VARCHAR(64) PRIMARY KEY,
    machine_name VARCHAR(255) NOT NULL,
    token VARCHAR(128) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ONLINE',
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    service_name VARCHAR(255) NOT NULL,
    agent_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_heartbeats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    agent_id VARCHAR(64) NOT NULL,
    cpu_percent DECIMAL(5,2) NOT NULL,
    ram_percent DECIMAL(5,2) NOT NULL,
    disk_percent DECIMAL(5,2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ONLINE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_heartbeats_agent_created (agent_id, created_at),
    CONSTRAINT fk_heartbeats_agent
        FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
        ON DELETE CASCADE
);

ALTER TABLE logs ADD COLUMN agent_id VARCHAR(64) NULL;
ALTER TABLE logs ADD COLUMN source_file VARCHAR(500) NULL;
ALTER TABLE logs ADD COLUMN received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
