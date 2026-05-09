import discord
from discord import app_commands
from discord.ext import commands
import lector
from app.config import settings
from app.services.player_service import PlayerService
from app.services.guild_config_service import GuildConfigService
from app.services.match_service import MatchService
from app.services.discord_setup_service import DiscordSetupService
from app.services.message_template_service import MessageTemplateService
from app.bot import formatting


_message_templates = MessageTemplateService()


def _txt(interaction: discord.Interaction, key: str, **kwargs) -> str:
    gid = str(interaction.guild.id) if interaction.guild else ""
    return _message_templates.render(gid, key, **kwargs)


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


def _command_allowed(interaction: discord.Interaction, cmd_key: str, channel_key: str) -> tuple[bool, str]:
    if not interaction.guild:
        return False, "solo_servidor"
    cfg = bot.guild_cfg_service.get_or_default(str(interaction.guild.id))
    if not cfg.get(f"{cmd_key}_enabled", 1):
        return False, "cmd_deshabilitado"

    require_channel = int(cfg.get(f"{cmd_key}_require_channel", 0)) == 1
    allowed = [c.strip() for c in (cfg.get(f"{cmd_key}_allowed_channels", "") or "").split(",") if c.strip()]
    if require_channel:
        if allowed:
            if str(interaction.channel_id) not in allowed:
                return False, "cmd_restringido_csv"
        elif not _in_config_channel(interaction, channel_key):
            return False, "cmd_restringido_canal"
    return True, ""


def _fmt(interaction: discord.Interaction, kind: str, message: str) -> str:
    """Todos los mensajes van con bloque ANSI (colores) según preset del servidor."""
    preset = "default"
    if interaction.guild:
        cfg = bot.guild_cfg_service.get_or_default(str(interaction.guild.id))
        preset = (cfg.get("ansi_preset") or "default").strip() or "default"
    return formatting.styled_message(preset, kind, message)


@app_commands.command(name="registrar", description="Registra tu nombre de juego.")
@app_commands.describe(nombre_steam="Tu nombre de Steam")
async def register(interaction: discord.Interaction, nombre_steam: str):
    allowed, tmpl = _command_allowed(interaction, "cmd_registrar", "channel_registro_id")
    if not allowed:
        await interaction.response.send_message(_fmt(interaction, "error", _txt(interaction, tmpl)), ephemeral=True)
        return
    created, name = bot.player_service.register(
        str(interaction.user.id),
        nombre_steam,
        guild_id=str(interaction.guild.id),
    )
    if not created:
        await interaction.response.send_message(_fmt(interaction, "warn", _txt(interaction, "registrar_ya")), ephemeral=True)
        return
    try:
        await interaction.user.edit(nick=name)
    except discord.Forbidden:
        pass
    await interaction.response.send_message(
        _fmt(interaction, "ok", _txt(interaction, "registrar_ok", name=name)),
    )


@app_commands.command(name="renombrar", description="Cambia tu nombre de juego.")
@app_commands.describe(nuevo_nombre="Nuevo nombre de juego")
async def rename(interaction: discord.Interaction, nuevo_nombre: str):
    allowed, tmpl = _command_allowed(interaction, "cmd_renombrar", "channel_registro_id")
    if not allowed:
        await interaction.response.send_message(_fmt(interaction, "error", _txt(interaction, tmpl)), ephemeral=True)
        return
    ok, name = bot.player_service.rename(
        str(interaction.user.id),
        nuevo_nombre,
        guild_id=str(interaction.guild.id),
    )
    if not ok:
        await interaction.response.send_message(
            _fmt(interaction, "error", _txt(interaction, "renombrar_no_reg")),
            ephemeral=True,
        )
        return
    try:
        await interaction.user.edit(nick=name)
    except discord.Forbidden:
        pass
    await interaction.response.send_message(_fmt(interaction, "ok", _txt(interaction, "renombrar_ok", name=name)))


@app_commands.command(name="perfil", description="Muestra tu perfil y MMR.")
async def profile(interaction: discord.Interaction):
    allowed, tmpl = _command_allowed(interaction, "cmd_perfil", "channel_general_id")
    if not allowed:
        await interaction.response.send_message(_fmt(interaction, "error", _txt(interaction, tmpl)), ephemeral=True)
        return
    from app.repositories.player_repository import PlayerRepository

    repo = PlayerRepository()
    row = repo.get_by_discord_id(str(interaction.user.id))
    if not row:
        await interaction.response.send_message(
            _fmt(interaction, "error", _txt(interaction, "perfil_no_reg")),
            ephemeral=True,
        )
        return
    repo.ensure_player_in_guild(str(interaction.user.id), str(interaction.guild.id))
    mmr_g = repo.get_mmr_for_guild(str(interaction.user.id), str(interaction.guild.id))
    mmr_show = round(mmr_g if mmr_g is not None else (row[2] or 400))
    await interaction.response.send_message(
        _fmt(
            interaction,
            "info",
            _txt(interaction, "perfil_ok", name=row[1], mmr=mmr_show),
        ),
    )


@app_commands.command(name="stickleaderboard", description="Muestra el top de jugadores.")
async def leaderboard(interaction: discord.Interaction):
    allowed, tmpl = _command_allowed(interaction, "cmd_stickleaderboard", "channel_historial_id")
    if not allowed:
        await interaction.response.send_message(_fmt(interaction, "error", _txt(interaction, tmpl)), ephemeral=True)
        return
    from app.repositories.player_repository import PlayerRepository

    top = PlayerRepository().top_players(15, guild_id=str(interaction.guild.id))
    if not top:
        await interaction.response.send_message(
            _fmt(interaction, "warn", _txt(interaction, "leaderboard_vacio")),
        )
        return
    lines = []
    for i, (name, mmr) in enumerate(top):
        lines.append(f"{i + 1}. {name} - {round(mmr)} MMR")
    body = _txt(interaction, "leaderboard_titulo") + "\n" + "\n".join(lines)
    await interaction.response.send_message(_fmt(interaction, "info", body))


@app_commands.command(name="partida", description="Sube captura para procesar partida.")
@app_commands.describe(host="Host de la partida (opcional)")
async def match(interaction: discord.Interaction, host: discord.Member | None = None):
    allowed, tmpl = _command_allowed(interaction, "cmd_partida", "channel_buzon_id")
    if not allowed:
        await interaction.response.send_message(_fmt(interaction, "error", _txt(interaction, tmpl)), ephemeral=True)
        return
    # Flujo fijo: solo imagen (primer attachment debe ser imagen si el usuario adjunta mas)
    if not interaction.attachments:
        await interaction.response.send_message(
            _fmt(interaction, "warn", _txt(interaction, "partida_no_imagen")),
            ephemeral=True,
        )
        return
    att = interaction.attachments[0]
    if not att.content_type or not att.content_type.startswith("image/"):
        await interaction.response.send_message(
            _fmt(interaction, "warn", _txt(interaction, "partida_formato")),
            ephemeral=True,
        )
        return
    await interaction.response.defer(thinking=True)
    gid = str(interaction.guild.id)
    cfg = bot.guild_cfg_service.get_or_default(gid)
    ocr_options = {
        "ocr_margin_percent": float(cfg.get("ocr_margin_percent", 20.0)),
        "ocr_corner_confidence": float(cfg.get("ocr_corner_confidence", 0.10)),
        "ocr_center_confidence": float(cfg.get("ocr_center_confidence", 0.25)),
        "ocr_color_distance_max": float(cfg.get("ocr_color_distance_max", 170.0)),
        "ocr_confidence_threshold": float(cfg.get("ocr_confidence_threshold", 0.25)),
    }
    try:
        image = await att.read()
        resultados = lector.analizar_captura(image, db_path=settings.database_path, ocr_options=ocr_options)
    except Exception as exc:  # noqa: BLE001
        err_msg = f"{type(exc).__name__}: {exc}"
        bot.guild_cfg_service.save(gid, {"last_ocr_error": err_msg[:500]})
        await interaction.followup.send(
            _fmt(interaction, "error", _txt(interaction, "partida_ocr_error")),
        )
        return

    min_points = int(cfg.get("ocr_min_points", 30))
    if not resultados or max(resultados.values()) < min_points:
        bot.guild_cfg_service.save(
            gid,
            {"last_ocr_error": "validacion: sin resultados o puntos bajo umbral ocr_min_points"},
        )
        await interaction.followup.send(_fmt(interaction, "error", _txt(interaction, "partida_sin_resultados")))
        return

    host_name = None
    if host:
        from app.repositories.player_repository import PlayerRepository

        row = PlayerRepository().get_by_discord_id(str(host.id))
        host_name = row[1] if row else None
    k_factor = float(cfg.get("mmr_k_factor", 32.0))
    host_penalty = float(cfg.get("host_penalty_percent", 8.0))
    adjusted, changes = bot.match_service.persist_match(
        resultados,
        host_name,
        k_factor=k_factor,
        host_penalty_percent=host_penalty,
        guild_id=gid,
    )
    bot.guild_cfg_service.save(gid, {"last_ocr_error": None})
    lines = []
    for jugador, puntos in sorted(adjusted.items(), key=lambda x: x[1], reverse=True):
        delta = round(changes[jugador])
        lines.append(f"{jugador}: {puntos} pts ({'+' if delta > 0 else ''}{delta} MMR)")
    msg = _txt(interaction, "partida_ok_prefijo") + "\n" + "\n".join(lines)
    sent = await interaction.followup.send(_fmt(interaction, "ok", msg))
    if int(cfg.get("partida_confirm_reaction", 0)) == 1 and sent:
        try:
            await sent.add_reaction("\u2705")
        except discord.HTTPException:
            pass


def run_bot():
    if not settings.discord_token:
        raise RuntimeError("Falta DISCORD_TOKEN en entorno.")
    bot.run(settings.discord_token)
