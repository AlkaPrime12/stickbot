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

    def create_player(self, discord_id: str, game_name: str):
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO jugadores (id_jugador, nombre_juego) VALUES (?, ?)",
                (discord_id, game_name),
            )

    def rename_player(self, discord_id: str, game_name: str):
        with get_connection() as conn:
            conn.execute(
                "UPDATE jugadores SET nombre_juego = ? WHERE id_jugador = ?",
                (game_name, discord_id),
            )

    def update_mmr(self, discord_id: str, mmr: float):
        with get_connection() as conn:
            conn.execute(
                "UPDATE jugadores SET mmr = ? WHERE id_jugador = ?",
                (mmr, discord_id),
            )

    def top_players(self, limit: int = 15):
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT nombre_juego, mmr FROM jugadores ORDER BY mmr DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return rows
