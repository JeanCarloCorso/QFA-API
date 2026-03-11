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

-- 3. Cria a tabela de avaliações do Screener (Motor Quantitativo)
CREATE TABLE IF NOT EXISTS stock_evaluations (
    ticker VARCHAR(20) PRIMARY KEY,
    sector VARCHAR(100),
    global_score DECIMAL(5,2),
    full_analysis_json JSON,
    last_updated DATE,
    selic_used DECIMAL(5,2),
    ipca_used DECIMAL(5,2),
    pib_used DECIMAL(5,2),
    
    INDEX idx_screener_sector (sector),
    INDEX idx_screener_score (global_score),
    INDEX idx_screener_updated (last_updated),
    
    CONSTRAINT fk_evaluations_company FOREIGN KEY (ticker) REFERENCES companies(ticker) ON DELETE CASCADE
);
