ALTER TABLE guild_config ADD COLUMN timezone TEXT DEFAULT 'UTC';
ALTER TABLE guild_config ADD COLUMN language TEXT DEFAULT 'es';

ALTER TABLE guild_config ADD COLUMN cmd_registrar_enabled INTEGER DEFAULT 1;
ALTER TABLE guild_config ADD COLUMN cmd_registrar_require_channel INTEGER DEFAULT 0;
ALTER TABLE guild_config ADD COLUMN cmd_registrar_allowed_channels TEXT DEFAULT '';

ALTER TABLE guild_config ADD COLUMN cmd_renombrar_enabled INTEGER DEFAULT 1;
ALTER TABLE guild_config ADD COLUMN cmd_renombrar_require_channel INTEGER DEFAULT 0;
ALTER TABLE guild_config ADD COLUMN cmd_renombrar_allowed_channels TEXT DEFAULT '';

ALTER TABLE guild_config ADD COLUMN cmd_perfil_enabled INTEGER DEFAULT 1;
ALTER TABLE guild_config ADD COLUMN cmd_perfil_require_channel INTEGER DEFAULT 0;
ALTER TABLE guild_config ADD COLUMN cmd_perfil_allowed_channels TEXT DEFAULT '';

ALTER TABLE guild_config ADD COLUMN cmd_stickleaderboard_enabled INTEGER DEFAULT 1;
ALTER TABLE guild_config ADD COLUMN cmd_stickleaderboard_require_channel INTEGER DEFAULT 0;
ALTER TABLE guild_config ADD COLUMN cmd_stickleaderboard_allowed_channels TEXT DEFAULT '';

ALTER TABLE guild_config ADD COLUMN cmd_partida_enabled INTEGER DEFAULT 1;
ALTER TABLE guild_config ADD COLUMN cmd_partida_require_channel INTEGER DEFAULT 0;
ALTER TABLE guild_config ADD COLUMN cmd_partida_allowed_channels TEXT DEFAULT '';

ALTER TABLE guild_config ADD COLUMN ansi_enabled INTEGER DEFAULT 1;
ALTER TABLE guild_config ADD COLUMN ocr_confidence_threshold REAL DEFAULT 0.25;
ALTER TABLE guild_config ADD COLUMN ocr_min_points INTEGER DEFAULT 30;
ALTER TABLE guild_config ADD COLUMN host_penalty_percent REAL DEFAULT 8.0;
