import datetime

from app.db import get_connection
from app.domain.mmr import calcular_cambios_mmr

_GPS_ENSURE = """
INSERT INTO guild_player_stats (guild_id, discord_user_id, mmr)
VALUES (:guild_id, :discord_user_id, 400.0)
ON CONFLICT (guild_id, discord_user_id) DO NOTHING
"""


class MatchService:
    def persist_match(
        self,
        resultados: dict,
        host_game_name: str | None = None,
        k_factor: float = 32.0,
        host_penalty_percent: float = 8.0,
        guild_id: str | None = None,
    ):
        if not guild_id:
            raise ValueError("guild_id es obligatorio para MMR por servidor.")

        adjusted = dict(resultados)
        if host_game_name and host_game_name in adjusted:
            pct = host_penalty_percent / 100.0
            descuento = round(adjusted[host_game_name] * pct)
            adjusted[host_game_name] -= descuento

        gid = str(guild_id)

        with get_connection() as conn:
            mmr_actuales = {}
            for jugador in adjusted:
                row = conn.execute(
                    "SELECT id_jugador FROM jugadores WHERE nombre_juego = :name",
                    {"name": jugador},
                ).fetchone()
                if not row:
                    continue
                discord_uid = row._mapping["id_jugador"]
                conn.execute(
                    _GPS_ENSURE,
                    {"guild_id": gid, "discord_user_id": str(discord_uid)},
                )
                r2 = conn.execute(
                    """
                    SELECT mmr FROM guild_player_stats
                    WHERE guild_id = :guild_id AND discord_user_id = :uid
                    """,
                    {"guild_id": gid, "uid": str(discord_uid)},
                ).fetchone()
                mmr_actuales[jugador] = float(r2._mapping["mmr"]) if r2 else 400.0

            cambios = calcular_cambios_mmr(adjusted, mmr_actuales, k_factor=k_factor)

            now = datetime.datetime.now()
            rid = conn.execute(
                """
                INSERT INTO partidas (fecha, guild_id) VALUES (:fecha, :guild_id)
                RETURNING id_partida
                """,
                {"fecha": now.isoformat(timespec="seconds"), "guild_id": gid},
            ).scalar_one()
            id_partida = int(rid)

            for jugador, puntos in adjusted.items():
                row = conn.execute(
                    "SELECT id_jugador FROM jugadores WHERE nombre_juego = :name",
                    {"name": jugador},
                ).fetchone()
                if not row:
                    continue
                discord_id = row._mapping["id_jugador"]
                conn.execute(
                    _GPS_ENSURE,
                    {"guild_id": gid, "discord_user_id": str(discord_id)},
                )
                nuevo_mmr = mmr_actuales[jugador] + cambios[jugador]
                conn.execute(
                    """
                    UPDATE guild_player_stats SET mmr = :mmr
                    WHERE guild_id = :guild_id AND discord_user_id = :uid
                    """,
                    {"mmr": nuevo_mmr, "guild_id": gid, "uid": str(discord_id)},
                )
                conn.execute(
                    """
                    UPDATE jugadores SET mmr = :mmr WHERE id_jugador = :id
                    """,
                    {"mmr": nuevo_mmr, "id": str(discord_id)},
                )
                conn.execute(
                    """
                    INSERT INTO detalles_partida (id_partida, id_jugador, puntos)
                    VALUES (:id_partida, :id_jugador, :puntos)
                    """,
                    {"id_partida": id_partida, "id_jugador": discord_id, "puntos": puntos},
                )

        return adjusted, cambios
