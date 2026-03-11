CREATE DATABASE IF NOT EXISTS qfa_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE qfa_db;

-- 2. Cria a tabela de empresas (Ativos da B3 para o Screener)
CREATE TABLE IF NOT EXISTS companies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL UNIQUE,
    company_name VARCHAR(255) NOT NULL,
    sector VARCHAR(100) NOT NULL,
    subsector VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Índices para otimizar as buscas por setor na API
    INDEX idx_sector (sector),
    INDEX idx_subsector (subsector)
);

-- 3. Insere alguns dados mocks iniciais
INSERT INTO companies (ticker, company_name, sector, subsector) VALUES 
('WEGE3.SA', 'WEG S.A.', 'Industrials', 'Electrical Equipment'),
('ITUB4.SA', 'Itaú Unibanco Holding S.A.', 'Financial Services', 'Banks'),
('VALE3.SA', 'Vale S.A.', 'Basic Materials', 'Other Industrial Metals & Mining'),
('PETR4.SA', 'Petróleo Brasileiro S.A.', 'Energy', 'Oil & Gas Integrated'),
('ABEV3.SA', 'Ambev S.A.', 'Consumer Defensive', 'Beverages Non-Alcoholic')
ON DUPLICATE KEY UPDATE updated_at=CURRENT_TIMESTAMP;
