from app.repositories.player_repository import PlayerRepository


class PlayerService:
    def __init__(self):
        self.repo = PlayerRepository()

    def register(self, discord_id: str, game_name: str):
        game_name = game_name[:15]
        existing = self.repo.get_by_discord_id(discord_id)
        if existing:
            return False, game_name
        self.repo.create_player(discord_id, game_name)
        return True, game_name

    def rename(self, discord_id: str, game_name: str):
        game_name = game_name[:15]
        existing = self.repo.get_by_discord_id(discord_id)
        if not existing:
            return False, game_name
        self.repo.rename_player(discord_id, game_name)
        return True, game_name
