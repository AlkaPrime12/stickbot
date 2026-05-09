CREATE TABLE IF NOT EXISTS guild_config (
    guild_id TEXT PRIMARY KEY,
    channel_buzon_id TEXT,
    channel_registro_id TEXT,
    channel_historial_id TEXT,
    channel_general_id TEXT,
    channel_busqueda_id TEXT,
    role_buscando_id TEXT,
    cooldown_minutes INTEGER DEFAULT 22,
    daily_limit INTEGER DEFAULT 3,
    auto_mode INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS guild_admins (
    guild_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    PRIMARY KEY (guild_id, user_id)
);

CREATE TABLE IF NOT EXISTS setup_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    setup_mode TEXT NOT NULL,
    report_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bot_permissions_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    channel_id TEXT,
    capability TEXT NOT NULL,
    status TEXT NOT NULL,
    detail TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_limite_fecha ON limite_diario(fecha);
CREATE INDEX IF NOT EXISTS idx_setup_runs_guild ON setup_runs(guild_id);
