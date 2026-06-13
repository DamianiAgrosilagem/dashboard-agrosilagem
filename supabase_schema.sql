-- ============================================================
--  Damiani Agrosilagem — CRM Schema
--  Executar no SQL Editor do Supabase
-- ============================================================

-- Habilita extensão UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─── CLIENTES ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS clientes (
    id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    nome            TEXT NOT NULL,
    cpf_cnpj        TEXT,
    email           TEXT,
    telefone        TEXT,
    whatsapp        TEXT,
    cidade          TEXT,
    estado          TEXT DEFAULT 'RS',
    endereco        TEXT,
    lat             DOUBLE PRECISION,
    lng             DOUBLE PRECISION,
    segmento        TEXT DEFAULT 'Agro',
    classificacao   TEXT DEFAULT 'B' CHECK (classificacao IN ('A','B','C')),
    observacoes     TEXT,
    responsavel     TEXT,
    ativo           BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─── INTERAÇÕES ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS interacoes (
    id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    cliente_id  UUID NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    tipo        TEXT NOT NULL CHECK (tipo IN ('visita','ligacao','whatsapp','email','anotacao')),
    data_hora   TIMESTAMPTZ DEFAULT NOW(),
    responsavel TEXT,
    resultado   TEXT,
    observacoes TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ─── TAREFAS / FOLLOW-UPS ────────────────────────────────────
CREATE TABLE IF NOT EXISTS tarefas (
    id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    cliente_id  UUID NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    titulo      TEXT NOT NULL,
    descricao   TEXT,
    prazo       TIMESTAMPTZ,
    responsavel TEXT,
    status      TEXT DEFAULT 'pendente' CHECK (status IN ('pendente','concluida','cancelada')),
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ─── ÍNDICES ─────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_clientes_nome        ON clientes(nome);
CREATE INDEX IF NOT EXISTS idx_clientes_cidade      ON clientes(cidade);
CREATE INDEX IF NOT EXISTS idx_clientes_classif     ON clientes(classificacao);
CREATE INDEX IF NOT EXISTS idx_interacoes_cliente   ON interacoes(cliente_id);
CREATE INDEX IF NOT EXISTS idx_interacoes_data      ON interacoes(data_hora DESC);
CREATE INDEX IF NOT EXISTS idx_tarefas_cliente      ON tarefas(cliente_id);
CREATE INDEX IF NOT EXISTS idx_tarefas_prazo        ON tarefas(prazo);
CREATE INDEX IF NOT EXISTS idx_tarefas_status       ON tarefas(status);

-- ─── AUTO updated_at ─────────────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER clientes_updated_at
    BEFORE UPDATE ON clientes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE OR REPLACE TRIGGER tarefas_updated_at
    BEFORE UPDATE ON tarefas
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ─── RLS (opcional, habilitar depois de configurar auth) ─────
-- ALTER TABLE clientes ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE interacoes ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE tarefas ENABLE ROW LEVEL SECURITY;
