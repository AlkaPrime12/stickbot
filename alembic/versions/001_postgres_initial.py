"""Esquema inicial Postgres (StickBot)."""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001_postgres_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "jugadores",
        sa.Column("id_jugador", sa.Text(), nullable=False),
        sa.Column("nombre_juego", sa.Text(), nullable=True),
        sa.Column("mmr", sa.Float(), server_default="400"),
        sa.Column("sigma", sa.Float(), server_default="500"),
        sa.PrimaryKeyConstraint("id_jugador"),
    )
    op.create_table(
        "guild_config",
        sa.Column("guild_id", sa.Text(), nullable=False),
        sa.Column("channel_buzon_id", sa.Text(), nullable=True),
        sa.Column("channel_registro_id", sa.Text(), nullable=True),
        sa.Column("channel_historial_id", sa.Text(), nullable=True),
        sa.Column("channel_general_id", sa.Text(), nullable=True),
        sa.Column("channel_busqueda_id", sa.Text(), nullable=True),
        sa.Column("role_buscando_id", sa.Text(), nullable=True),
        sa.Column("cooldown_minutes", sa.Integer(), server_default="22"),
        sa.Column("daily_limit", sa.Integer(), server_default="3"),
        sa.Column("auto_mode", sa.Integer(), server_default="0"),
        sa.Column("timezone", sa.Text(), server_default="UTC"),
        sa.Column("language", sa.Text(), server_default="es"),
        sa.Column("cmd_registrar_enabled", sa.Integer(), server_default="1"),
        sa.Column("cmd_registrar_require_channel", sa.Integer(), server_default="0"),
        sa.Column("cmd_registrar_allowed_channels", sa.Text(), server_default=""),
        sa.Column("cmd_renombrar_enabled", sa.Integer(), server_default="1"),
        sa.Column("cmd_renombrar_require_channel", sa.Integer(), server_default="0"),
        sa.Column("cmd_renombrar_allowed_channels", sa.Text(), server_default=""),
        sa.Column("cmd_perfil_enabled", sa.Integer(), server_default="1"),
        sa.Column("cmd_perfil_require_channel", sa.Integer(), server_default="0"),
        sa.Column("cmd_perfil_allowed_channels", sa.Text(), server_default=""),
        sa.Column("cmd_stickleaderboard_enabled", sa.Integer(), server_default="1"),
        sa.Column("cmd_stickleaderboard_require_channel", sa.Integer(), server_default="0"),
        sa.Column("cmd_stickleaderboard_allowed_channels", sa.Text(), server_default=""),
        sa.Column("cmd_partida_enabled", sa.Integer(), server_default="1"),
        sa.Column("cmd_partida_require_channel", sa.Integer(), server_default="0"),
        sa.Column("cmd_partida_allowed_channels", sa.Text(), server_default=""),
        sa.Column("ansi_enabled", sa.Integer(), server_default="1"),
        sa.Column("ocr_confidence_threshold", sa.Float(), server_default="0.25"),
        sa.Column("ocr_min_points", sa.Integer(), server_default="30"),
        sa.Column("host_penalty_percent", sa.Float(), server_default="8"),
        sa.Column("guild_display_name", sa.Text(), server_default=""),
        sa.Column("limits_apply_non_admin_only", sa.Integer(), server_default="0"),
        sa.Column("bot_admin_ids", sa.Text(), server_default=""),
        sa.Column("mmr_k_factor", sa.Float(), server_default="32"),
        sa.Column("partida_confirm_reaction", sa.Integer(), server_default="0"),
        sa.Column("ocr_margin_percent", sa.Float(), server_default="20"),
        sa.Column("ocr_center_confidence", sa.Float(), server_default="0.25"),
        sa.Column("ocr_corner_confidence", sa.Float(), server_default="0.1"),
        sa.Column("ocr_color_distance_max", sa.Float(), server_default="170"),
        sa.Column("last_ocr_error", sa.Text(), nullable=True),
        sa.Column("ansi_preset", sa.Text(), server_default="default"),
        sa.PrimaryKeyConstraint("guild_id"),
    )
    op.create_table(
        "partidas",
        sa.Column(
            "id_partida",
            sa.Integer(),
            sa.Identity(always=False),
            nullable=False,
        ),
        sa.Column("fecha", sa.DateTime(timezone=False), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("guild_id", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id_partida"),
    )
    op.create_table(
        "detalles_partida",
        sa.Column(
            "id_partida",
            sa.Integer(),
            sa.ForeignKey("partidas.id_partida", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("id_jugador", sa.Text(), sa.ForeignKey("jugadores.id_jugador"), nullable=False),
        sa.Column("puntos", sa.Integer(), nullable=False),
    )
    op.create_table(
        "limite_diario",
        sa.Column("id_jugador", sa.Text(), nullable=False),
        sa.Column("usos", sa.Integer(), server_default="0"),
        sa.Column("fecha", sa.Text(), nullable=True),
        sa.Column("ultimo_uso", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id_jugador"),
    )
    op.create_table(
        "guild_admins",
        sa.Column("guild_id", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("guild_id", "user_id"),
    )
    op.create_table(
        "setup_runs",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("guild_id", sa.Text(), nullable=False),
        sa.Column("setup_mode", sa.Text(), nullable=False),
        sa.Column("report_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "bot_permissions_audit",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("guild_id", sa.Text(), nullable=False),
        sa.Column("channel_id", sa.Text(), nullable=True),
        sa.Column("capability", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "guild_player_stats",
        sa.Column("guild_id", sa.Text(), nullable=False),
        sa.Column("discord_user_id", sa.Text(), sa.ForeignKey("jugadores.id_jugador"), nullable=False),
        sa.Column("mmr", sa.Float(), server_default="400"),
        sa.PrimaryKeyConstraint("guild_id", "discord_user_id"),
    )
    op.create_table(
        "guild_message_templates",
        sa.Column("guild_id", sa.Text(), nullable=False),
        sa.Column("template_key", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), server_default="", nullable=False),
        sa.PrimaryKeyConstraint("guild_id", "template_key"),
    )

    op.create_index("idx_gps_guild_mmr", "guild_player_stats", ["guild_id", "mmr"])
    op.create_index("idx_gps_mmr", "guild_player_stats", ["mmr"])
    op.create_index("idx_jugadores_nombre_juego", "jugadores", ["nombre_juego"])
    op.create_index("idx_gps_discord_user", "guild_player_stats", ["discord_user_id"])
    op.create_index("idx_limite_fecha", "limite_diario", ["fecha"])
    op.create_index("idx_setup_runs_guild", "setup_runs", ["guild_id"])


def downgrade() -> None:
    op.drop_index("idx_setup_runs_guild", table_name="setup_runs")
    op.drop_index("idx_limite_fecha", table_name="limite_diario")
    op.drop_index("idx_gps_discord_user", table_name="guild_player_stats")
    op.drop_index("idx_jugadores_nombre_juego", table_name="jugadores")
    op.drop_index("idx_gps_mmr", table_name="guild_player_stats")
    op.drop_index("idx_gps_guild_mmr", table_name="guild_player_stats")

    op.drop_table("guild_message_templates")
    op.drop_table("guild_player_stats")
    op.drop_table("bot_permissions_audit")
    op.drop_table("setup_runs")
    op.drop_table("guild_admins")
    op.drop_table("limite_diario")
    op.drop_table("detalles_partida")
    op.drop_table("partidas")
    op.drop_table("guild_config")
    op.drop_table("jugadores")
