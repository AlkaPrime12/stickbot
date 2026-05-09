from app.db import get_connection


class PlayerRepository:
    def get_by_discord_id(self, discord_id: str):
        with get_connection() as conn:
            row = conn.execute(
                "SELECT id_jugador, nombre_juego, mmr FROM jugadores WHERE id_jugador = ?",
                (discord_id,),
            ).fetchone()
            return row

    def get_by_game_name(self, game_name: str):
        with get_connection() as conn:
            row = conn.execute(
                "SELECT id_jugador, nombre_juego, mmr FROM jugadores WHERE nombre_juego = ?",
                (game_name,),
            ).fetchone()
            return row

    def get_mmr_for_guild(self, discord_id: str, guild_id: str) -> float | None:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT mmr FROM guild_player_stats
                WHERE guild_id = ? AND discord_user_id = ?
                """,
                (str(guild_id), str(discord_id)),
            ).fetchone()
            return float(row[0]) if row else None

    def create_player(self, discord_id: str, game_name: str, guild_id: str | None = None):
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO jugadores (id_jugador, nombre_juego) VALUES (?, ?)",
                (discord_id, game_name),
            )
            if guild_id:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO guild_player_stats (guild_id, discord_user_id, mmr)
                    VALUES (?, ?, 400.0)
                    """,
                    (str(guild_id), str(discord_id)),
                )

    def ensure_guild_stat(self, guild_id: str, discord_id: str, default_mmr: float = 400.0):
        with get_connection() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO guild_player_stats (guild_id, discord_user_id, mmr)
                VALUES (?, ?, ?)
                """,
                (str(guild_id), str(discord_id), default_mmr),
            )

    def ensure_player_in_guild(self, discord_id: str, guild_id: str) -> None:
        """Si el jugador existe globalmente pero no en este guild, crea fila copiando mmr de jugadores."""
        with get_connection() as conn:
            ex = conn.execute(
                """
                SELECT 1 FROM guild_player_stats
                WHERE guild_id = ? AND discord_user_id = ?
                """,
                (str(guild_id), str(discord_id)),
            ).fetchone()
            if ex:
                return
            j = conn.execute(
                "SELECT mmr FROM jugadores WHERE id_jugador = ?",
                (str(discord_id),),
            ).fetchone()
            mmr = float(j[0]) if j else 400.0
            conn.execute(
                """
                INSERT INTO guild_player_stats (guild_id, discord_user_id, mmr)
                VALUES (?, ?, ?)
                """,
                (str(guild_id), str(discord_id), mmr),
            )

    def rename_player(self, discord_id: str, game_name: str):
        with get_connection() as conn:
            conn.execute(
                "UPDATE jugadores SET nombre_juego = ? WHERE id_jugador = ?",
                (game_name, discord_id),
            )

    def update_mmr_global(self, discord_id: str, mmr: float):
        """Legacy: sincroniza jugadores.mmr por compat. Preferir update_mmr_guild."""
        with get_connection() as conn:
            conn.execute(
                "UPDATE jugadores SET mmr = ? WHERE id_jugador = ?",
                (mmr, discord_id),
            )

    def update_mmr_guild(self, guild_id: str, discord_id: str, mmr: float):
        with get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO guild_player_stats (guild_id, discord_user_id, mmr)
                VALUES (?, ?, ?)
                """,
                (str(guild_id), str(discord_id), float(mmr)),
            )

    def top_players(self, limit: int = 15, guild_id: str | None = None, offset: int = 0):
        with get_connection() as conn:
            if guild_id is not None:
                rows = conn.execute(
                    """
                    SELECT j.nombre_juego, gs.mmr
                    FROM guild_player_stats gs
                    JOIN jugadores j ON j.id_jugador = gs.discord_user_id
                    WHERE gs.guild_id = ?
                    ORDER BY gs.mmr DESC
                    LIMIT ? OFFSET ?
                    """,
                    (str(guild_id), limit, offset),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT j.nombre_juego, mmr FROM jugadores ORDER BY mmr DESC LIMIT ? OFFSET ?
                    """,
                    (limit, offset),
                ).fetchall()
            return rows

    def top_players_global(self, limit: int = 50, offset: int = 0):
        """Ranking mundial: todas las filas guild_player_stats (un jugador puede aparecer en varios guilds)."""
        with get_connection() as conn:
            return conn.execute(
                """
                SELECT gs.guild_id,
                    CASE
                        WHEN gs.guild_id = '_legacy_' THEN 'Legacy'
                        ELSE COALESCE(NULLIF(TRIM(gc.guild_display_name), ''), gs.guild_id)
                    END AS gname,
                    j.nombre_juego, COALESCE(gs.mmr, 400.0) AS mmr
                FROM guild_player_stats gs
                JOIN jugadores j ON j.id_jugador = gs.discord_user_id
                LEFT JOIN guild_config gc ON gc.guild_id = gs.guild_id
                ORDER BY gs.mmr DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ).fetchall()

    def count_global_rows(self) -> int:
        with get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) FROM guild_player_stats").fetchone()
            return int(row[0]) if row else 0
