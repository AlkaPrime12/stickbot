import discord
from discord import app_commands
from discord.ext import commands
import lector
from app.config import settings
from app.services.player_service import PlayerService
from app.services.guild_config_service import GuildConfigService
from app.services.match_service import MatchService
from app.services.discord_setup_service import DiscordSetupService


class StickBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
        self.player_service = PlayerService()
        self.guild_cfg_service = GuildConfigService()
        self.match_service = MatchService()
        self.discord_setup_service = DiscordSetupService()

    async def setup_hook(self):
        self.tree.add_command(register)
        self.tree.add_command(rename)
        self.tree.add_command(profile)
        self.tree.add_command(leaderboard)
        self.tree.add_command(match)
        await self.tree.sync()


bot = StickBot()


@bot.event
async def on_guild_join(guild: discord.Guild):
    # Auto-configure channels and role when bot is added to a server.
    try:
        channels, role_id, _report = await bot.discord_setup_service.auto_setup(str(guild.id))
        bot.guild_cfg_service.save(
            str(guild.id),
            {
                **channels,
                "role_buscando_id": role_id,
                "cooldown_minutes": settings.default_cooldown_minutes,
                "daily_limit": settings.default_daily_limit,
                "auto_mode": 1,
            },
        )
    except Exception:
        # If bot lacks permissions, setup can still be done manually via web.
        pass


def _in_config_channel(interaction: discord.Interaction, key: str) -> bool:
    if not interaction.guild:
        return False
    cfg = bot.guild_cfg_service.get_or_default(str(interaction.guild.id))
    channel_id = cfg.get(key)
    return channel_id is None or int(channel_id) == interaction.channel_id


@app_commands.command(name="registrar", description="Registra tu nombre de juego.")
@app_commands.describe(nombre_steam="Tu nombre de Steam")
async def register(interaction: discord.Interaction, nombre_steam: str):
    if not _in_config_channel(interaction, "channel_registro_id"):
        await interaction.response.send_message("Este comando solo se permite en el canal de registro configurado.", ephemeral=True)
        return
    created, name = bot.player_service.register(str(interaction.user.id), nombre_steam)
    if not created:
        await interaction.response.send_message("Ya estas registrado.", ephemeral=True)
        return
    try:
        await interaction.user.edit(nick=name)
    except discord.Forbidden:
        pass
    await interaction.response.send_message(f"Registrado como **{name}** con 400 MMR iniciales.")


@app_commands.command(name="renombrar", description="Cambia tu nombre de juego.")
@app_commands.describe(nuevo_nombre="Nuevo nombre de juego")
async def rename(interaction: discord.Interaction, nuevo_nombre: str):
    ok, name = bot.player_service.rename(str(interaction.user.id), nuevo_nombre)
    if not ok:
        await interaction.response.send_message("No estas registrado. Usa /registrar primero.", ephemeral=True)
        return
    try:
        await interaction.user.edit(nick=name)
    except discord.Forbidden:
        pass
    await interaction.response.send_message(f"Nombre actualizado a **{name}**.")


@app_commands.command(name="perfil", description="Muestra tu perfil y MMR.")
async def profile(interaction: discord.Interaction):
    from app.repositories.player_repository import PlayerRepository

    repo = PlayerRepository()
    row = repo.get_by_discord_id(str(interaction.user.id))
    if not row:
        await interaction.response.send_message("No estas registrado. Usa /registrar.", ephemeral=True)
        return
    await interaction.response.send_message(f"Jugador: **{row[1]}** | MMR: **{round(row[2])}**")


@app_commands.command(name="stickleaderboard", description="Muestra el top de jugadores.")
async def leaderboard(interaction: discord.Interaction):
    from app.repositories.player_repository import PlayerRepository

    top = PlayerRepository().top_players(15)
    if not top:
        await interaction.response.send_message("No hay jugadores registrados.")
        return
    lines = []
    for i, (name, mmr) in enumerate(top):
        lines.append(f"{i + 1}. {name} - {round(mmr)} MMR")
    await interaction.response.send_message("🏆 Leaderboard\n" + "\n".join(lines))


@app_commands.command(name="partida", description="Sube captura para procesar partida.")
@app_commands.describe(host="Host de la partida (opcional)")
async def match(interaction: discord.Interaction, host: discord.Member | None = None):
    if not _in_config_channel(interaction, "channel_buzon_id"):
        await interaction.response.send_message("Este comando solo se permite en el canal de partidas configurado.", ephemeral=True)
        return
    if not interaction.attachments:
        await interaction.response.send_message("Adjunta la captura de resultado.", ephemeral=True)
        return
    await interaction.response.defer(thinking=True)
    image = await interaction.attachments[0].read()
    resultados = lector.analizar_captura(image)
    if not resultados:
        await interaction.followup.send("No se detectaron resultados validos.")
        return
    host_name = None
    if host:
        from app.repositories.player_repository import PlayerRepository

        row = PlayerRepository().get_by_discord_id(str(host.id))
        host_name = row[1] if row else None
    adjusted, changes = bot.match_service.persist_match(resultados, host_name)
    lines = []
    for jugador, puntos in sorted(adjusted.items(), key=lambda x: x[1], reverse=True):
        delta = round(changes[jugador])
        lines.append(f"{jugador}: {puntos} pts ({'+' if delta > 0 else ''}{delta} MMR)")
    await interaction.followup.send("Partida procesada:\n" + "\n".join(lines))


def run_bot():
    if not settings.discord_token:
        raise RuntimeError("Falta DISCORD_TOKEN en entorno.")
    bot.run(settings.discord_token)
