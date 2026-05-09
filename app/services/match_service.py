import datetime
from app.db import get_connection
from app.domain.mmr import calcular_cambios_mmr


class MatchService:
    def persist_match(self, resultados: dict, host_game_name: str | None = None):
        adjusted = dict(resultados)
        if host_game_name and host_game_name in adjusted:
            descuento = round(adjusted[host_game_name] * 0.08)
            adjusted[host_game_name] -= descuento

        with get_connection() as conn:
            mmr_actuales = {}
            for jugador in adjusted:
                row = conn.execute(
                    "SELECT mmr FROM jugadores WHERE nombre_juego = ?",
                    (jugador,),
                ).fetchone()
                mmr_actuales[jugador] = row[0] if row else 400.0

            cambios = calcular_cambios_mmr(adjusted, mmr_actuales)
            conn.execute("INSERT INTO partidas (fecha) VALUES (?)", (str(datetime.datetime.now()),))
            id_partida = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

            for jugador, puntos in adjusted.items():
                row = conn.execute(
                    "SELECT id_jugador FROM jugadores WHERE nombre_juego = ?",
                    (jugador,),
                ).fetchone()
                if not row:
                    continue
                discord_id = row[0]
                nuevo_mmr = mmr_actuales[jugador] + cambios[jugador]
                conn.execute("UPDATE jugadores SET mmr = ? WHERE id_jugador = ?", (nuevo_mmr, discord_id))
                conn.execute(
                    "INSERT INTO detalles_partida (id_partida, id_jugador, puntos) VALUES (?, ?, ?)",
                    (id_partida, discord_id, puntos),
                )

        return adjusted, cambios
