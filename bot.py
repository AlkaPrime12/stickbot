import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import sqlite3
import lector
import datetime
import asyncio

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True # ¡Línea nueva crucial para ver quién entra!

bot = commands.Bot(command_prefix='!', intents=intents)

# =========================================================
# ⚙️ CONSTANTES GLOBALES (Fáciles de editar en el futuro)
# =========================================================
ID_CANAL_BUZON = 1498150653632184411
ID_CANAL_REGISTRO = 1497825515061645333
ID_CANAL_HISTORIAL = 1498001541972623611
ADMINS = [523218278680625152, 610244496763912202, 631546632688631828]

# --- BLINDAJE DE RUTA DE BASE DE DATOS ---
DIRECTORIO_BASE = os.path.dirname(os.path.abspath(__file__))
RUTA_DB = os.path.join(DIRECTORIO_BASE, 'stickbot.db')
# Añade el canal general o de bienvenida a tus globales
ID_CANAL_GENERAL = 1495238536931180698 # Reemplaza con la ID de tu chat general
ID_ROL_BUSCANDO = 1497816934060785876
SEGUNDOS_EXPIRACION_ROL = 10800

rol_expiration_tasks = {}

def conectar_db():
    return sqlite3.connect(RUTA_DB, timeout=10.0)

@bot.event
async def on_ready():
    print(f'¡Éxito! El bot {bot.user.name} está conectado y listo para rankear.')



@bot.event
async def on_member_join(member):
    canal_general = bot.get_channel(ID_CANAL_GENERAL)
    if canal_general:
        mensaje = (
            f"🥊 ¡Bienvenido a la arena, {member.mention}!\n\n"
            f"**PASO OBLIGATORIO:** Para poder jugar y rankear, ve al canal <#{ID_CANAL_REGISTRO}> "
            f"y escribe el comando `!registrar TuNombreDeSteam`.\n"
            f"*(Ejemplo: `!registrar Guizeenhoo`)*\n\n"
            f"El bot automáticamente cambiará tu apodo en este servidor para que coincida con tu cuenta de Steam y te dará tus 400 MMR iniciales."
        )
        await canal_general.send(mensaje)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # 1. Guardia del Buzón de Partidas
    if message.channel.id == ID_CANAL_BUZON:
        if not message.content.lower().startswith('!partida'):
            await message.delete()
            try:
                await message.channel.send(f"⚠️ {message.author.mention}, este canal es exclusivo para subir resultados. Solo se permite el comando `!partida`.", delete_after=7.0)
            except discord.Forbidden:
                pass
            return

    # 2. Guardia del Canal de Registros
    if message.channel.id == ID_CANAL_REGISTRO:
        if not message.content.lower().startswith('!registrar'):
            await message.delete()
            try:
                await message.channel.send(f"⚠️ {message.author.mention}, este canal es exclusivo para registros. Solo se permite el comando `!registrar`.", delete_after=7.0)
            except discord.Forbidden:
                pass
            return

    await bot.process_commands(message)

@bot.command()
async def registrar(ctx, *, nombre_steam: str = None):
    # 1. Guardia de canal
    if ctx.channel.id != ID_CANAL_REGISTRO:
        mensaje_error = await ctx.send(f"🛑 {ctx.author.mention}, el registro solo se puede hacer en el canal <#{1497825515061645333}>.")
        await asyncio.sleep(5)
        await ctx.message.delete()
        await mensaje_error.delete()
        return

    # 2. Verificar que el usuario haya escrito su nombre
    if not nombre_steam:
        mensaje_ayuda = await ctx.send(f"⚠️ {ctx.author.mention}, debes incluir tu nombre exacto de Steam.\n**Uso correcto:** `!registrar TuNombre`")
        await asyncio.sleep(10)
        try:
            await ctx.message.delete()
            await mensaje_ayuda.delete()
        except discord.Forbidden:
            pass
        return

    # 3. Límite estricto de Stick Fight (15 caracteres)
    nombre_juego = nombre_steam[:15]

    # 4. Conexión a la base de datos con tu timeout de seguridad
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute('SELECT * FROM jugadores WHERE id_jugador = ?', (str(ctx.author.id),))
    
    if cursor.fetchone():
        await ctx.send(f'⚠️ {ctx.author.mention}, ya estás registrado en la base de datos.')
    else:
        # 5. Intentar sincronizar el apodo en Discord
        nota_apodo = ""
        try:
            await ctx.author.edit(nick=nombre_juego)
            nota_apodo = f"y tu apodo fue actualizado a **{nombre_juego}**"
        except discord.Forbidden:
            nota_apodo = "*(Nota: Cámbiate el apodo a mano en el servidor, no tengo permisos suficientes)*"

        # 6. Inserción final
        cursor.execute('INSERT INTO jugadores (id_jugador, nombre_juego) VALUES (?, ?)', (str(ctx.author.id), nombre_juego))
        conexion.commit() 
        await ctx.send(f'✅ Registrado automáticamente como **{nombre_juego}** con los 400 MMR iniciales {nota_apodo}.')
    
    conexion.close()

@bot.command(aliases=['cambiarnombre', 'rename'])
async def renombrar(ctx, *, nuevo_nombre: str = None):
    # 1. Verificar que el usuario haya escrito su nuevo nombre
    if not nuevo_nombre:
        await ctx.send(f"⚠️ {ctx.author.mention}, debes escribir tu nuevo nombre de Steam.\n**Uso correcto:** `!renombrar TuNuevoNombre`")
        return

    # 2. Mantener el límite de 15 caracteres del Stick Fight
    nombre_juego = nuevo_nombre[:15]

    # 3. Conexión a la base de datos
    conexion = conectar_db()
    cursor = conexion.cursor()
    
    # 4. Verificar si el jugador existe en la base de datos
    cursor.execute('SELECT * FROM jugadores WHERE id_jugador = ?', (str(ctx.author.id),))
    if not cursor.fetchone():
        await ctx.send(f'❌ {ctx.author.mention}, no estás registrado en el sistema. Debes usar el comando `!registrar` primero.')
        conexion.close()
        return

    # 5. Actualizar SOLO el nombre (El MMR y el historial quedan intactos)
    cursor.execute('UPDATE jugadores SET nombre_juego = ? WHERE id_jugador = ?', (nombre_juego, str(ctx.author.id)))
    conexion.commit()
    conexion.close()

    # 6. Intentar sincronizar el apodo en Discord
    nota_apodo = ""
    try:
        await ctx.author.edit(nick=nombre_juego)
        nota_apodo = f"y tu apodo en el servidor ha sido sincronizado"
    except discord.Forbidden:
        nota_apodo = "*(Nota: Cámbiate el apodo a mano en el servidor, no tengo permisos suficientes para hacerlo)*"

    # 7. Mensaje de confirmación
    await ctx.send(f'🔄 ¡Cambio exitoso! {ctx.author.mention}, tu nombre de jugador ahora es **{nombre_juego}** {nota_apodo}. Tus MMR siguen intactos.')

def calcular_cambios_mmr(resultados_partida, mmr_actuales):
    K = 32
    cambios = {jugador: 0 for jugador in resultados_partida}
    jugadores = list(resultados_partida.keys())
    for i in range(len(jugadores)):
        for j in range(i + 1, len(jugadores)):
            jug_a, jug_b = jugadores[i], jugadores[j]
            res_a = 1 if resultados_partida[jug_a] > resultados_partida[jug_b] else (0 if resultados_partida[jug_a] < resultados_partida[jug_b] else 0.5)
            res_b = 1 - res_a
            exp_a = 1 / (1 + 10 ** ((mmr_actuales[jug_b] - mmr_actuales[jug_a]) / 400))
            exp_b = 1 / (1 + 10 ** ((mmr_actuales[jug_a] - mmr_actuales[jug_b]) / 400))
            cambios[jug_a] += K * (res_a - exp_a)
            cambios[jug_b] += K * (res_b - exp_b)
    return cambios

@bot.command()
async def partida(ctx, host_mencionado: discord.Member = None):
    if ctx.channel.id != ID_CANAL_BUZON:
        mensaje_error = await ctx.send(f"🛑 {ctx.author.mention}, los resultados solo se pueden subir en el canal <#{ID_CANAL_BUZON}>.")
        await asyncio.sleep(5)
        await ctx.message.delete()
        await mensaje_error.delete()
        return

    COOLDOWN_MINUTOS = 22
    es_vip = ctx.author.id in ADMINS or ctx.author.guild_permissions.administrator
    ahora = datetime.datetime.now()
    fecha_hoy = str(ahora.date())

    if not es_vip:
        conexion = conectar_db()
        cursor = conexion.cursor()
        cursor.execute('SELECT usos, fecha, ultimo_uso FROM limite_diario WHERE id_jugador = ?', (str(ctx.author.id),))
        registro = cursor.fetchone()

        if not registro:
            cursor.execute(
                'INSERT INTO limite_diario (id_jugador, usos, fecha, ultimo_uso) VALUES (?, 0, ?, NULL)',
                (str(ctx.author.id), fecha_hoy),
            )
            conexion.commit()
            usos, f_guardada, u_uso = (0, fecha_hoy, None)
        else:
            usos, f_guardada, u_uso = registro
            if f_guardada != fecha_hoy:
                cursor.execute(
                    'UPDATE limite_diario SET usos = 0, fecha = ?, ultimo_uso = NULL WHERE id_jugador = ?',
                    (fecha_hoy, str(ctx.author.id)),
                )
                conexion.commit()
                usos, f_guardada, u_uso = (0, fecha_hoy, None)

        if u_uso:
            try:
                u_uso_dt = datetime.datetime.fromisoformat(u_uso)
            except ValueError:
                u_uso_dt = None

            if u_uso_dt and (ahora - u_uso_dt).total_seconds() / 60 < COOLDOWN_MINUTOS:
                restante = round(COOLDOWN_MINUTOS - (ahora - u_uso_dt).total_seconds() / 60)
                await ctx.send(f"⏳ Espera **{restante} min** para enviar otra captura.")
                conexion.close()
                return

        if usos >= 3:
            await ctx.send("🛑 Límite diario de 3 partidas alcanzado.")
            conexion.close()
            return
        conexion.close()

    if not ctx.message.attachments:
        await ctx.send("⚠️ Adjunta la imagen del resultado.")
        return

    mensaje_espera = await ctx.send("🔍 Analizando captura... un momento.")
    adjunto = ctx.message.attachments[0]
    imagen_bytes = await adjunto.read()
    resultados = lector.analizar_captura(imagen_bytes)

    if not resultados or max(resultados.values()) < 30:
        await mensaje_espera.edit(content="⚠️ Captura inválida (jugadores no registrados o menos de 30 pts).")
        return

    target_host_id = str(host_mencionado.id) if host_mencionado else str(ctx.author.id)
    host_real_user = host_mencionado if host_mencionado else ctx.author

    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute('SELECT nombre_juego FROM jugadores WHERE id_jugador = ?', (target_host_id,))
    fila_host = cursor.fetchone()
    conexion.close()

    nombre_juego_host = fila_host[0] if fila_host else None

    if nombre_juego_host in resultados:
        solicitud = await ctx.send(f"⚠️ **ATENCIÓN:** Se ha detectado a {host_real_user.mention} como Host. \nReacciona con ✅ a este mensaje para confirmar y aplicar el nivelamiento.")
        await solicitud.add_reaction("✅")
        
        def check_reaccion(reaction, user):
            return user.id == host_real_user.id and reaction.message.id == solicitud.id and str(reaction.emoji) == "✅"

        try:
            reaccion, usuario_reaccion = await bot.wait_for('reaction_add', timeout=300.0, check=check_reaccion)
        except asyncio.TimeoutError:
            await solicitud.edit(content="❌ Tiempo de espera agotado (5 minutos). Partida cancelada.")
            await solicitud.clear_reactions()
            return
    else:
        await ctx.send("ℹ️ No se detectó al host mencionado en la imagen. Se procesará sin penalización.")

    conexion = conectar_db()
    cursor = conexion.cursor()
    
    detalles_puntos_texto = {} 
    for jugador in resultados:
        puntos_originales = resultados[jugador]
        if jugador == nombre_juego_host:
            # BUG ARREGLADO: 0.08 = 8% de penalización
            descuento = round(puntos_originales * 0.08)
            resultados[jugador] = puntos_originales - descuento
            detalles_puntos_texto[jugador] = f"{puntos_originales} pts ➔ Nivelación Host (-{descuento} pts) ➔ **{resultados[jugador]}**"
        else:
            detalles_puntos_texto[jugador] = f"{puntos_originales} pts"

    mmr_actuales = {j: (cursor.execute('SELECT mmr FROM jugadores WHERE nombre_juego = ?', (j,)).fetchone() or (400.0,))[0] for j in resultados}
    cambios_mmr = calcular_cambios_mmr(resultados, mmr_actuales)
    
    cursor.execute('INSERT INTO partidas DEFAULT VALUES')
    id_partida = cursor.lastrowid
    
    texto_res = f"🏆 **RESULTADOS Y RANGOS** 🏆\n📅 {ahora.strftime('%d/%m/%Y %H:%M')}\n\n"
    res_ordenados = sorted(resultados.items(), key=lambda x: x[1], reverse=True)
    
    for jugador, puntos_finales in res_ordenados:
        nuevo_mmr = mmr_actuales[jugador] + cambios_mmr[jugador]
        cursor.execute('SELECT id_jugador FROM jugadores WHERE nombre_juego = ?', (jugador,))
        fila_db = cursor.fetchone()
        
        signo = "+" if cambios_mmr[jugador] > 0 else ""
        
        if fila_db:
            id_db = fila_db[0]
            cursor.execute('UPDATE jugadores SET mmr = ? WHERE id_jugador = ?', (nuevo_mmr, id_db))
            cursor.execute('INSERT INTO detalles_partida (id_partida, id_jugador, puntos) VALUES (?, ?, ?)', (id_partida, id_db, puntos_finales))
            texto_res += f"🎮 **{jugador}**: {detalles_puntos_texto.get(jugador, f'{puntos_finales} pts')} ➔ MMR: **{round(nuevo_mmr)}** ({signo}{round(cambios_mmr[jugador])})\n"
        else:
            texto_res += f"👻 **{jugador}** *(No registrado)*: {detalles_puntos_texto.get(jugador, f'{puntos_finales} pts')} \n"
            
    if not es_vip:
        cursor.execute(
            'UPDATE limite_diario SET usos = usos + 1, fecha = ?, ultimo_uso = ? WHERE id_jugador = ?',
            (fecha_hoy, ahora.isoformat(), str(ctx.author.id)),
        )
    
    conexion.commit()
    conexion.close()

    canal_hist = bot.get_channel(ID_CANAL_HISTORIAL)
    if canal_hist:
        await canal_hist.send(texto_res)
        await mensaje_espera.edit(content=f"✅ ¡Análisis completado! Ver en {canal_hist.mention}")
    else:
        await mensaje_espera.edit(content=texto_res)

@bot.command()
async def perfil(ctx):
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute('SELECT nombre_juego, mmr FROM jugadores WHERE id_jugador = ?', (str(ctx.author.id),))
    jugador = cursor.fetchone()

    if not jugador:
        await ctx.send('⚠️ No estás registrado en el sistema. Usa `!registrar` para empezar.')
        conexion.close()
        return

    nombre, mmr = jugador

    cursor.execute('SELECT COUNT(*) + 1 FROM jugadores WHERE mmr > ?', (mmr,))
    posicion = cursor.fetchone()[0]

    fecha_hoy = str(datetime.date.today())
    cursor.execute('SELECT usos FROM limite_diario WHERE id_jugador = ? AND fecha = ?', (str(ctx.author.id), fecha_hoy))
    registro_uso = cursor.fetchone()
    usos_hoy = registro_uso[0] if registro_uso else 0

    mensaje = (
        f"👤 **HOJA DE PERSONAJE: {ctx.author.display_name}**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎮 **Nombre en Juego:** {nombre}\n"
        f"🏆 **MMR Actual:** `{round(mmr)}` puntos\n"
        f"🥇 **Posición en el Ranking:** `#{posicion}`\n"
        f"📅 **Partidas hoy:** `{usos_hoy}/3` registradas\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"*¡Sigue peleando para llegar al Top 1!*"
    )
    
    await ctx.send(mensaje)
    conexion.close()

@bot.command(aliases=['ranking', 'top', 'leaderboard'])
async def stickleaderboard(ctx):
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute('SELECT nombre_juego, mmr FROM jugadores ORDER BY mmr DESC LIMIT 15')
    top = cursor.fetchall()
    conexion.close()

    if not top:
        await ctx.send("⚠️ No hay jugadores registrados aún.")
        return

    res = "🏆 **LEADERBOARD OFICIAL** 🏆\n\n"
    for i, (nombre, mmr) in enumerate(top):
        medalla = "🥇" if i==0 else ("🥈" if i==1 else ("🥉" if i==2 else f"**{i+1}.**"))
        res += f"{medalla} **{nombre}** ➔ {round(mmr)} MMR\n"
        
    await ctx.send(res)

    # Asegúrate de poner este bloque al final de tu bot.py, antes de bot.run(TOKEN)

class LFGView(discord.ui.View):
    def __init__(self, host, timeout=1800): # 1800 segundos = 30 minutos
        super().__init__(timeout=timeout)
        self.host = host
        self.jugadores = [host] # El creador entra automáticamente
        self.mensaje = None # Guardaremos la referencia al mensaje aquí

    async def actualizar_embed(self, interaction: discord.Interaction):
        # Actualiza la lista de jugadores visualmente
        embed = interaction.message.embeds[0]
        lista = "\n".join([f"⚔️ {j.mention}" for j in self.jugadores])
        embed.description = f"**Jugadores en sala ({len(self.jugadores)}/4):**\n{lista}"
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="¡Me apunto!", style=discord.ButtonStyle.green, custom_id="join_btn")
    async def boton_unirse(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.jugadores:
            await interaction.response.send_message("Ya estás en la lista.", ephemeral=True)
            return

        self.jugadores.append(interaction.user)

        # Si llegamos a 4 jugadores
        if len(self.jugadores) == 4:
            # Apagamos los botones
            for child in self.children:
                child.disabled = True
            
            # Actualizamos el color y texto a "Listo"
            embed = interaction.message.embeds[0]
            lista = "\n".join([f"⚔️ {j.mention}" for j in self.jugadores])
            embed.title = "🔥 ¡PARTIDA LLENA! 🔥"
            embed.color = discord.Color.gold()
            embed.description = f"**Los 4 luchadores son:**\n{lista}"
            await interaction.response.edit_message(embed=embed, view=self)
            
            # Etiquetamos a todos en el canal
            pings = " ".join([j.mention for j in self.jugadores])
            await interaction.channel.send(f"🚨 ¡SALA LISTA! {pings}\nPónganse de acuerdo y envíen el código de Steam.")
            self.stop() # Detenemos el reloj del bot
        else:
            await self.actualizar_embed(interaction)

    @discord.ui.button(label="Ya no puedo", style=discord.ButtonStyle.red, custom_id="leave_btn")
    async def boton_salir(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user == self.host:
            await interaction.response.send_message("Eres el host. Si cancelas, elimina el mensaje.", ephemeral=True)
            return
            
        if interaction.user in self.jugadores:
            self.jugadores.remove(interaction.user)
            await self.actualizar_embed(interaction)
        else:
            await interaction.response.send_message("No estabas en la lista.", ephemeral=True)

    async def on_timeout(self):
        # Esto ocurre automáticamente si pasan 30 minutos y no se llenó
        for child in self.children:
            child.disabled = True
        
        if self.mensaje:
            embed = self.mensaje.embeds[0]
            embed.title = "❌ Búsqueda expirada"
            embed.color = discord.Color.dark_gray()
            embed.set_footer(text="El tiempo límite de 30 minutos se agotó.")
            try:
                await self.mensaje.edit(embed=embed, view=self)
            except discord.HTTPException:
                pass

@bot.command(aliases=['resetmmr', 'nuevatemporada'])
async def reiniciartemporada(ctx):
    # 1. Seguridad: Verificar si el usuario está en la lista global de ADMINS
    if ctx.author.id not in ADMINS:
        await ctx.send("⛔ ¡Acceso denegado! Este comando es de uso exclusivo para los dueños del bot.")
        return

    # 2. Doble factor de seguridad: Confirmación por reacción
    mensaje = await ctx.send(
        "⚠️ **¡ADVERTENCIA DE REINICIO DE TEMPORADA!** ⚠️\n"
        "Estás a punto de resetear el MMR de **TODOS** los jugadores a 400.\n"
        "Reacciona con 💣 a este mensaje en los próximos 15 segundos para confirmar la aniquilación de los rangos."
    )
    await mensaje.add_reaction("💣")

    def check(reaction, user):
        return user.id == ctx.author.id and str(reaction.emoji) == "💣" and reaction.message.id == mensaje.id

    try:
        # Esperamos a que el admin reaccione
        await bot.wait_for('reaction_add', timeout=15.0, check=check)
    except asyncio.TimeoutError:
        # Si pasan 15 segundos y no reacciona, se cancela para proteger la BD
        await ctx.send("❌ Tiempo de confirmación agotado. Operación cancelada, los MMR están a salvo.")
        return

    # 3. Ejecución del reseteo masivo en la base de datos
    conexion = conectar_db()
    cursor = conexion.cursor()
    
    # Al no usar WHERE, esta instrucción actualiza TODAS las filas de la tabla
    cursor.execute('UPDATE jugadores SET mmr = 400')
    
    # (Opcional) Limpiamos también el límite diario para que la gente 
    # pueda jugar de inmediato al iniciar la temporada sin importar si ya habían jugado hoy.
    cursor.execute('UPDATE limite_diario SET usos = 0') 
    
    conexion.commit()
    conexion.close()

    # 4. Anuncio oficial
    await ctx.send("🔄 **¡NUEVA TEMPORADA INICIADA!** 🔄\nEl ranking ha sido limpiado. ¡Todos los luchadores vuelven a la línea de salida con 400 MMR!")

async def quitar_rol_automaticamente(guild_id, user_id, role_id, delay_seconds):
    try:
        await asyncio.sleep(delay_seconds)
        guild = bot.get_guild(guild_id)
        if guild is None:
            return

        miembro = guild.get_member(user_id)
        rol = guild.get_role(role_id)
        if miembro is None or rol is None or rol not in miembro.roles:
            return

        await miembro.remove_roles(rol)
        try:
            await miembro.send("⏰ Tu rol de **Buscando Partida** en el servidor ha expirado tras 3 horas. ¡Usa `!rol` si quieres activarlo de nuevo!")
        except discord.Forbidden:
            pass
    finally:
        rol_expiration_tasks.pop(user_id, None)

@bot.command()
async def rol(ctx):
    # Borramos el comando para mantener limpio el chat
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass

    rol = ctx.guild.get_role(ID_ROL_BUSCANDO)

    if not rol:
        return # Seguridad por si la ID del rol está mal

    # Si el usuario YA TIENE el rol, se lo quitamos manualmente
    if rol in ctx.author.roles:
        await ctx.author.remove_roles(rol)
        tarea = rol_expiration_tasks.pop(ctx.author.id, None)
        if tarea:
            tarea.cancel()
        await ctx.send(f"🔕 {ctx.author.mention}, te he quitado el rol. Ya no te llegarán notificaciones.", delete_after=5.0)
    
    # Si NO TIENE el rol, se lo damos y empezamos la cuenta regresiva
    else:
        await ctx.author.add_roles(rol)
        await ctx.send(f"🔔 {ctx.author.mention}, rol activado. Se te quitará automáticamente en 3 horas.", delete_after=5.0)

        tarea_anterior = rol_expiration_tasks.get(ctx.author.id)
        if tarea_anterior:
            tarea_anterior.cancel()

        rol_expiration_tasks[ctx.author.id] = asyncio.create_task(
            quitar_rol_automaticamente(ctx.guild.id, ctx.author.id, ID_ROL_BUSCANDO, SEGUNDOS_EXPIRACION_ROL)
        )

@bot.command(aliases=['bp', 'lfg'])
async def buscarpartida(ctx):
    # --- LIMPIEZA DEL CHAT ---
    try:
        await ctx.message.delete() # Esto borra el "!buscarpartida" del usuario
    except discord.Forbidden:
        pass # Ignora el error si el bot por alguna razón no tiene permisos

    ID_CANAL_BUSQUEDA = 1500528020547571752 
    
    embed = discord.Embed(
        title="🎮 ¡Buscando partida de Stick Fight!",
        description=f"**Jugadores en sala (1/4):**\n⚔️ {ctx.author.mention}",
        color=discord.Color.blue()
    )
    embed.set_footer(text="Esta búsqueda se cancelará sola en 30 minutos.")
    
    vista = LFGView(host=ctx.author)
    
    # Enviamos el mensaje con los botones y guardamos la referencia
    mensaje = await ctx.send(f"<@&1497816934060785876> ¡{ctx.author.display_name} busca gente!", embed=embed, view=vista)
    vista.mensaje = mensaje # Le pasamos el mensaje a la vista para el timeout

if not TOKEN:
    raise RuntimeError("Falta DISCORD_TOKEN en el entorno. Crea un archivo .env con DISCORD_TOKEN=tu_token.")

bot.run(TOKEN)