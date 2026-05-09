from __future__ import annotations

from app.db import get_connection


_GPS_UPSERT = """
INSERT INTO guild_player_stats (guild_id, discord_user_id, mmr)
VALUES (:guild_id, :discord_user_id, :mmr)
ON CONFLICT (guild_id, discord_user_id) DO UPDATE SET mmr = EXCLUDED.mmr
"""

_GPS_INSERT_IGNORE = """
INSERT INTO guild_player_stats (guild_id, discord_user_id, mmr)
VALUES (:guild_id, :discord_user_id, :mmr)
ON CONFLICT (guild_id, discord_user_id) DO NOTHING
"""


class PlayerRepository:
    def list_all_game_names(self) -> list[str]:
        """Nombres de juego conocidos para matching OCR."""
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT nombre_juego FROM jugadores WHERE nombre_juego IS NOT NULL ORDER BY nombre_juego",
                {},
            ).fetchall()
            return [str(r._mapping["nombre_juego"]) for r in rows if r._mapping.get("nombre_juego")]

    def get_by_discord_id(self, discord_id: str):
        with get_connection() as conn:
            row = conn.execute(
                "SELECT id_jugador, nombre_juego, mmr FROM jugadores WHERE id_jugador = :id",
                {"id": discord_id},
            ).fetchone()
            return (row[0], row[1], row[2]) if row else None

    def get_by_game_name(self, game_name: str):
        with get_connection() as conn:
            row = conn.execute(
                "SELECT id_jugador, nombre_juego, mmr FROM jugadores WHERE nombre_juego = :name",
                {"name": game_name},
            ).fetchone()
            return (row[0], row[1], row[2]) if row else None

    def get_mmr_for_guild(self, discord_id: str, guild_id: str) -> float | None:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT mmr FROM guild_player_stats
                WHERE guild_id = :guild_id AND discord_user_id = :uid
                """,
                {"guild_id": str(guild_id), "uid": str(discord_id)},
            ).fetchone()
            return float(row._mapping["mmr"]) if row else None

    def create_player(self, discord_id: str, game_name: str, guild_id: str | None = None):
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO jugadores (id_jugador, nombre_juego) VALUES (:id, :name)",
                {"id": discord_id, "name": game_name},
            )
            if guild_id:
                conn.execute(
                    _GPS_UPSERT,
                    {"guild_id": str(guild_id), "discord_user_id": str(discord_id), "mmr": 400.0},
                )

    def ensure_guild_stat(self, guild_id: str, discord_id: str, default_mmr: float = 400.0):
        with get_connection() as conn:
            conn.execute(
                _GPS_INSERT_IGNORE,
                {"guild_id": str(guild_id), "discord_user_id": str(discord_id), "mmr": float(default_mmr)},
            )

    def ensure_player_in_guild(self, discord_id: str, guild_id: str) -> None:
        """Si el jugador existe globalmente pero no en este guild, crea fila copiando mmr de jugadores."""
        with get_connection() as conn:
            ex = conn.execute(
                """
                SELECT 1 AS x FROM guild_player_stats
                WHERE guild_id = :guild_id AND discord_user_id = :uid
                """,
                {"guild_id": str(guild_id), "uid": str(discord_id)},
            ).fetchone()
            if ex:
                return
            j = conn.execute(
                "SELECT mmr FROM jugadores WHERE id_jugador = :uid",
                {"uid": str(discord_id)},
            ).fetchone()
            mmr = float(j._mapping["mmr"]) if j else 400.0
            conn.execute(
                _GPS_INSERT_IGNORE,
                {"guild_id": str(guild_id), "discord_user_id": str(discord_id), "mmr": mmr},
            )

    def rename_player(self, discord_id: str, game_name: str):
        with get_connection() as conn:
            conn.execute(
                "UPDATE jugadores SET nombre_juego = :name WHERE id_jugador = :id",
                {"name": game_name, "id": discord_id},
            )

    def update_mmr_global(self, discord_id: str, mmr: float):
        """Legacy: sincroniza jugadores.mmr por compat. Preferir update_mmr_guild."""
        with get_connection() as conn:
            conn.execute(
                "UPDATE jugadores SET mmr = :mmr WHERE id_jugador = :id",
                {"mmr": mmr, "id": discord_id},
            )

    def update_mmr_guild(self, guild_id: str, discord_id: str, mmr: float):
        with get_connection() as conn:
            conn.execute(
                _GPS_UPSERT,
                {
                    "guild_id": str(guild_id),
                    "discord_user_id": str(discord_id),
                    "mmr": float(mmr),
                },
            )

    def top_players(self, limit: int = 15, guild_id: str | None = None, offset: int = 0):
        with get_connection() as conn:
            if guild_id is not None:
                rows = conn.execute(
                    """
                    SELECT j.nombre_juego, gs.mmr
                    FROM guild_player_stats gs
                    JOIN jugadores j ON j.id_jugador = gs.discord_user_id
                    WHERE gs.guild_id = :guild_id
                    ORDER BY gs.mmr DESC
                    LIMIT :lim OFFSET :off
                    """,
                    {"guild_id": str(guild_id), "lim": limit, "off": offset},
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT nombre_juego, mmr FROM jugadores ORDER BY mmr DESC LIMIT :lim OFFSET :off
                    """,
                    {"lim": limit, "off": offset},
                ).fetchall()
            return [tuple(r) for r in rows]

    def top_players_global(self, limit: int = 50, offset: int = 0):
        """Ranking mundial: todas las filas guild_player_stats (un jugador puede aparecer en varios guilds)."""
        with get_connection() as conn:
            rows = conn.execute(
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
                LIMIT :lim OFFSET :off
                """,
                {"lim": limit, "off": offset},
            ).fetchall()
            return [
                (
                    r._mapping["guild_id"],
                    r._mapping["gname"],
                    r._mapping["nombre_juego"],
                    r._mapping["mmr"],
                )
                for r in rows
            ]

    def count_global_rows(self) -> int:
        with get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM guild_player_stats", {}).fetchone()
            return int(row._mapping["c"]) if row else 0
