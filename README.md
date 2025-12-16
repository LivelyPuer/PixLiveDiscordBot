# PixLive Discord & Telegram Bot

Async Discord bot that posts new DeviantArt posts to a specified channel, with an administrative Telegram bot (password-protected) for control and analytics. Config is read from `.env`.

## 🚀 Quick Deploy (Production)

**Deploy everything with one command:**

```bash
curl -fsSL https://raw.githubusercontent.com/LivelyPuer/PixLiveDiscordBot/main/install.sh | sudo bash
```

Automatically:
- ✅ Installs all dependencies (Python, git, build tools)
- ✅ Clones repo to `/opt/PixLiveDiscordBot`
- ✅ Creates Python virtual environment
- ✅ **Sets up auto-start via systemd**
- ✅ **Auto-restarts if bot crashes**

👉 **[Quick Start Guide](QUICKSTART.md)** | **[Full Deployment](DEPLOYMENT.md)** | **[Scripts Doc](SCRIPTS_FULL.md)**

## 🏃 Local Quick Start

```bash
bash run.sh
```

The script will setup everything and run the bot.

## 📋 Manual Quickstart

- copy `.env.example` to `.env` and fill tokens
- set `DEVIANTART_USERNAMES` in `.env` to a comma-separated list (e.g. `artist1,artist2`)
- install deps: `pip install -r requirements.txt`
- run: `python main.py`

## Features

- Poll DeviantArt RSS feeds and post new deviations to Discord
- Extensible services architecture (add more services)
- Telegram admin bot with password-based auth for controlling services and viewing analytics
- 🔄 Auto-start on server reboot
- 🔁 Auto-restart on crash

## 📚 Documentation

| File | Purpose |
|------|---------|
| [QUICKSTART.md](QUICKSTART.md) | Quick deployment guide |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Full deployment guide |
| [SCRIPTS_FULL.md](SCRIPTS_FULL.md) | All scripts documentation |
| [SETUP.md](SETUP.md) | How to get API tokens |
| [SCRIPTS.md](SCRIPTS.md) | Legacy scripts info |

