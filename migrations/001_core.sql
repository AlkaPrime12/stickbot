CREATE TABLE IF NOT EXISTS jugadores (
    id_jugador TEXT PRIMARY KEY,
    nombre_juego TEXT,
    mmr REAL DEFAULT 400.0,
    sigma REAL DEFAULT 500.0
);

CREATE TABLE IF NOT EXISTS partidas (
    id_partida INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS detalles_partida (
    id_partida INTEGER,
    id_jugador TEXT,
    puntos INTEGER,
    FOREIGN KEY(id_partida) REFERENCES partidas(id_partida),
    FOREIGN KEY(id_jugador) REFERENCES jugadores(id_jugador)
);

CREATE TABLE IF NOT EXISTS limite_diario (
    id_jugador TEXT PRIMARY KEY,
    usos INTEGER DEFAULT 0,
    fecha TEXT,
    ultimo_uso TEXT
);
