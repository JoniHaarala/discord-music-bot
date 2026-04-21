## 🎵 Discord Music Bot (Python)

A Discord music bot that plays audio from YouTube using `yt-dlp` and `FFmpeg`. It supports voice channel playback, a per-server queue system, and basic playback controls.

---

## 🚀 Features

- Play audio from YouTube URLs
- Per-server music queue
- Auto-play next track in queue
- Simple voice channel control
- Auto-connection to voice channels
- Stream support with automatic reconnection

---

## 📦 Requirements

Before running the bot, make sure you have:

- Python 3.12+
- `ffmpeg` installed and added to PATH
- A Discord bot application with a valid token. Visit Discord dev portal (https://discord.com/developers/home) for more info. 

---

## 📥 Installation

1. Clone this repository:

```bash
git clone https://github.com/JoniHaarala/discord-music-bot.git
cd discord-music-bot
````

<!--2. Install dependencies:

```bash
pip install -r requirements.txt
``` -->

2. Install dependencies:

```bash
pip install discord.py yt-dlp python-dotenv
```

3. Create a `.env` file in the project root:

```env
DISCORD_TOKEN=your_bot_token_here
```

---

## ▶️ Running the Bot

Start the bot with:

```bash
python main.py
```

---

## 🎮 Commands

| Command       | Description                                               |
| ------------- | --------------------------------------------------------- |
| `!join`       | Bot joins your voice channel                              |
| `!play <url>` | Plays music from YouTube or adds it to the queue          |
| `!skip`       | Skips the current track                                   |
| `!queue`      | Displays the current queue                                |
| `!stop`       | Stops playback, clears the queue, and disconnects the bot |

---

## ⚙️ How It Works

* If nothing is playing, `!play` starts playback immediately.
* If a track is already playing, use `!play` to add a new songs to a server-specific queue playlist.
* When a song ends, the next one in the queue is automatically played.
* `yt-dlp` extracts audio from YouTube.
* `FFmpeg` handles audio streaming in Discord voice channels.

---

## 🧠 Project Structure

```
.
├── bot.py
├── .env
└── README.md
```

---

## ⚠️ Important Notes

* FFmpeg is required for audio playback to work.
* You must enable the `message content intent` in the Discord Developer Portal.
* YouTube changes may affect `yt-dlp`, so keep it updated regularly.

---

## 📜 License

This project is free to use for personal and educational purposes. Commercial porpuses are not allowed.

---

## ✨ Author Notes

Built with Python 3.12.x, discord.py, and yt-dlp
