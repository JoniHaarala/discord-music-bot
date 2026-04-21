import discord
from discord.ext import commands
import yt_dlp
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

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

queues = {}


def check_queue(ctx, server_id):
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
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))

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


# @bot.command(name='stop')
# async def stop(ctx):
#     await ctx.voice_client.disconnect()

@bot.command(name='stop')
async def stop(ctx):
    server_id = ctx.guild.id
    if server_id in queues:
        queues[server_id] = []  # Limpiar cola
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Desconectado y playlist vaciada.")


@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user.name}')


bot.run(TOKEN)
