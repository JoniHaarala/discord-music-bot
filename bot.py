import os
import re
import yt_dlp
import asyncio
from dotenv import load_dotenv
import discord
from discord.ext import commands
import spotifyHandler

queues = {}
load_dotenv()

# Configuracion de credenciales
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Configuración de YT-DLP
yt_dlp.utils.bug_reports_message = lambda *args, **kwargs: ''
ytdl_format_options = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
}
ffmpeg_options = {
    'options': '-vn',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)


def limpiar_texto(text: str) -> str:
    # Reemplaza todo lo que no sea letras, números o espacios
    return re.sub(r'[^a-zA-Z0-9\s]', '', text)


async def check_queue(ctx, server_id):
    if server_id in queues and queues[server_id]:
        # Sacamos la siguiente canción
        player = queues[server_id].pop(0)
        ctx.voice_client.play(player, after=lambda e: check_queue(ctx, server_id))
        # Enviamos un mensaje (opcional, requiere usar un thread-safe method o simplemente dejar que suene)
        print(f"Reproduciendo siguiente: {player.title}")
        ctx.send(f"Reproduciendo siguiente: {player.title}")


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()

        # Si no es un link de YouTube o Spotify, le añadimos el prefijo de búsqueda
        if not url.startswith('http'):
            search_query = f"ytsearch:{url}"
        else:
            search_query = url

        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(search_query, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


# Configuración del Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.command(name='join')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("¡Debes estar en un canal de voz!")
        return
    channel = ctx.message.author.voice.channel
    await channel.connect()


@bot.command(name='play')
async def play(ctx, url):
    if ctx.voice_client is None:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            return await ctx.send("¡Entra a un canal de voz!")

    server_id = ctx.guild.id

    # --- LÓGICA PARA PLAYLISTS (YouTube / YT Music) ---
    # Detectamos si el link contiene "list=" que es el estándar de playlists
    if "list=" in url:
        await ctx.send("📝 Detectada una playlist de YT. Procesando canciones...")

        # Configuramos yt-dlp para extraer la información de la lista sin descargar
        ydl_opts_playlist = {'extract_flat': True, 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts_playlist) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'entries' in info:
                entries = list(info['entries'])
                await ctx.send(f"✅ Se han encontrado **{len(entries)}** canciones.")

                for i, entry in enumerate(entries):
                    # El nombre o la URL del video
                    video_url = f"https://music.youtube.com/watch?v={entry['id']}"
                    player = await YTDLSource.from_url(video_url, loop=bot.loop, stream=True)

                    if i == 0 and not ctx.voice_client.is_playing():
                        ctx.voice_client.play(player, after=lambda e: check_queue(ctx, server_id))
                        await ctx.send(f"🎶 Reproduciendo ahora: **{player.title}**")
                    else:
                        if server_id not in queues:
                            queues[server_id] = []
                        queues[server_id].append(player)

                return await ctx.send(f"Se agregaron {len(entries) - 1} canciones adicionales a la cola.")

    # Lógica para SPOTIFY
    elif "open.spotify.com" in url:
        print("¡Detectado link de Spotify! Buscando audio equivalente...")
        if "playlist" in url:
            # await ctx.send("⌛ Procesando playlist de Spotify... esto puede tardar un poco.")
            # track_list = spotifyHandler.get_spotify_playlist_tracks(url)
            return await ctx.send("Lo lamento, pero la funcion de reproducir playlist's se encuentra momentaneamente desactivada 😔")
            if not track_list:
                return await ctx.send("No pude obtener canciones de esa playlist.")

            # Agregamos la primera canción de inmediato o a la cola
            for i, track_name in enumerate(track_list):
                player = await YTDLSource.from_url(track_name, loop=bot.loop, stream=True)

                if i == 0 and not ctx.voice_client.is_playing():
                    ctx.voice_client.play(player, after=lambda e: check_queue(ctx, server_id))
                    await ctx.send(f"🎶 Reproduciendo ahora: **{player.title}**")
                else:
                    if server_id not in queues: queues[server_id] = []
                    queues[server_id].append(player)

            return await ctx.send(f"✅ Se han añadido **{len(track_list)}** canciones a la cola.")

        elif "track" in url:
            track_info = limpiar_texto(spotifyHandler.get_spotify_track_info(url))
            if track_info:
                url = track_info  # Ahora 'search' es "Nombre Canción Artista"
            else:
                return await ctx.send("No pude obtener la información de Spotifysa WAW 😔")

    async with ctx.typing():
        try:
            player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
        except Exception as e:
            return await ctx.send(f"Error al procesar el video: {e}")

        if not ctx.voice_client.is_playing():
            # Si no hay nada sonando, toca ahora
            ctx.voice_client.play(player, after=lambda e: check_queue(ctx, server_id))
            await ctx.send(f'🎶 Reproduciendo ahora: **{player.title}**')
        else:
            # Si ya hay algo, se va a la cola
            if server_id not in queues:
                queues[server_id] = []
            queues[server_id].append(player)
            await ctx.send(f'📝 Añadido a la cola de reproduccion: **{player.title}**')


@bot.command(name='skip')
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()  # Esto activará automáticamente el 'after' del play actual
        await ctx.send("⏭️ Canción saltada.")
    else:
        await ctx.send("No hay nada reproduciéndose ahora mismo.")


@bot.command(name='queue')
async def view_queue(ctx):
    server_id = ctx.guild.id
    if server_id not in queues or not queues[server_id]:
        return await ctx.send("La cola está vacía.")

    list_str = "\n".join([f"{i + 1}. {p.title}" for i, p in enumerate(queues[server_id])])
    await ctx.send(f"**Cola de reproducción: **\n{list_str}")


@bot.command(name='stop')
async def stop(ctx):
    server_id = ctx.guild.id
    if server_id in queues:
        queues[server_id] = []  # Limpiar cola
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Bot Desconectado y playlist vaciada.")


@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user.name}')


bot.run(DISCORD_TOKEN)
