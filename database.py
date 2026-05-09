import sqlite3
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.db_migrations import ensure_all_post_schema


def inicializar_db(database_path: str | None = None):
    # Esto crea el archivo stickbot.db automáticamente si no existe
    directorio_base = os.path.dirname(os.path.abspath(__file__))
    ruta_db = database_path if database_path else os.path.join(directorio_base, "stickbot.db")
    db_dir = os.path.dirname(ruta_db)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conexion = sqlite3.connect(ruta_db)
    cursor = conexion.cursor()

    # Los Jugadores (Guarda el nivel de habilidad)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jugadores (
            id_jugador TEXT PRIMARY KEY,
            nombre_juego TEXT,
            mmr REAL DEFAULT 400.0,
            sigma REAL DEFAULT 500.0
        )
    ''')


    cursor.execute('''
        CREATE TABLE IF NOT EXISTS partidas (
            id_partida INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')


    cursor.execute('''
        CREATE TABLE IF NOT EXISTS detalles_partida (
            id_partida INTEGER,
            id_jugador TEXT,
            puntos INTEGER,
            FOREIGN KEY(id_partida) REFERENCES partidas(id_partida),
            FOREIGN KEY(id_jugador) REFERENCES jugadores(id_jugador)
        )
    ''')
    
# Tabla 4: Control Anti-Spam (Limita usos y añade Cooldown)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS limite_diario (
            id_jugador TEXT PRIMARY KEY,
            usos INTEGER DEFAULT 0,
            fecha TEXT,
            ultimo_uso TEXT -- Nueva columna para el cooldown
        )
    ''')

    # Configuracion por servidor (guild)
    cursor.execute('''
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
            auto_mode INTEGER DEFAULT 0,
            timezone TEXT DEFAULT 'UTC',
            language TEXT DEFAULT 'es',
            cmd_registrar_enabled INTEGER DEFAULT 1,
            cmd_registrar_require_channel INTEGER DEFAULT 0,
            cmd_registrar_allowed_channels TEXT DEFAULT '',
            cmd_renombrar_enabled INTEGER DEFAULT 1,
            cmd_renombrar_require_channel INTEGER DEFAULT 0,
            cmd_renombrar_allowed_channels TEXT DEFAULT '',
            cmd_perfil_enabled INTEGER DEFAULT 1,
            cmd_perfil_require_channel INTEGER DEFAULT 0,
            cmd_perfil_allowed_channels TEXT DEFAULT '',
            cmd_stickleaderboard_enabled INTEGER DEFAULT 1,
            cmd_stickleaderboard_require_channel INTEGER DEFAULT 0,
            cmd_stickleaderboard_allowed_channels TEXT DEFAULT '',
            cmd_partida_enabled INTEGER DEFAULT 1,
            cmd_partida_require_channel INTEGER DEFAULT 0,
            cmd_partida_allowed_channels TEXT DEFAULT '',
            ansi_enabled INTEGER DEFAULT 1,
            ocr_confidence_threshold REAL DEFAULT 0.25,
            ocr_min_points INTEGER DEFAULT 30,
            host_penalty_percent REAL DEFAULT 8.0,
            guild_display_name TEXT DEFAULT '',
            limits_apply_non_admin_only INTEGER DEFAULT 0,
            bot_admin_ids TEXT DEFAULT '',
            mmr_k_factor REAL DEFAULT 32.0,
            partida_confirm_reaction INTEGER DEFAULT 0,
            ocr_margin_percent REAL DEFAULT 20.0,
            ocr_center_confidence REAL DEFAULT 0.25,
            ocr_corner_confidence REAL DEFAULT 0.10,
            ocr_color_distance_max REAL DEFAULT 170.0,
            last_ocr_error TEXT,
            ansi_preset TEXT DEFAULT 'default'
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS guild_admins (
            guild_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            PRIMARY KEY (guild_id, user_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS setup_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT NOT NULL,
            setup_mode TEXT NOT NULL,
            report_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bot_permissions_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT NOT NULL,
            channel_id TEXT,
            capability TEXT NOT NULL,
            status TEXT NOT NULL,
            detail TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_limite_fecha ON limite_diario(fecha)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_setup_runs_guild ON setup_runs(guild_id)')
    ensure_all_post_schema(conexion)
    conexion.commit()
    conexion.close()
    print("¡Base de datos estructurada y lista para guardar los puntajes!")

if __name__ == '__main__':
    inicializar_db()