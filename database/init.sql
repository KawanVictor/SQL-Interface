-- MariaDB: charset e collation explícitos para suporte a acentos
CREATE DATABASE IF NOT EXISTS text_to_sql_mvp
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE text_to_sql_mvp;

CREATE TABLE IF NOT EXISTS logs (
    id               INT          AUTO_INCREMENT PRIMARY KEY,
    canal            VARCHAR(100) NOT NULL,
    equipamento      VARCHAR(100) NOT NULL,
    tipo_erro        VARCHAR(100) NOT NULL,
    descricao        TEXT,
    data_evento      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    duracao_segundos INT          UNSIGNED,
    severidade       ENUM('critico','alta','media','baixa') NOT NULL,
    -- índices dentro do CREATE TABLE: o MySQL não aceita CREATE INDEX IF NOT EXISTS
    INDEX idx_severidade  (severidade),
    INDEX idx_data_evento (data_evento),
    INDEX idx_canal       (canal),
    INDEX idx_equipamento (equipamento)
) ENGINE=InnoDB
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

INSERT INTO logs (canal, equipamento, tipo_erro, descricao, data_evento, duracao_segundos, severidade) VALUES
('Globo',     'Rewrapper-01', 'Perda de sinal', 'Falha crítica no sinal principal',  NOW() - INTERVAL 1 DAY,  12, 'critico'),
('SporTV',    'Rewrapper-02', 'Erro de áudio',  'Falha leve no canal de áudio',      NOW(),                    5, 'media'),
('Discovery', 'Rewrapper-01', 'Erro de vídeo',  'Travamento de frame',               NOW() - INTERVAL 3 DAY,   9, 'alta'),
('Globo',     'Rewrapper-03', 'Perda de sinal', 'Queda intermitente',                NOW() - INTERVAL 2 DAY,  20, 'alta'),
('Record',    'Rewrapper-02', 'Erro de áudio',  'Dessincronização A/V',              NOW() - INTERVAL 5 DAY,   3, 'media'),
('Band',      'Rewrapper-01', 'Erro de vídeo',  'Artefatos visuais detectados',      NOW() - INTERVAL 1 DAY,  15, 'critico');