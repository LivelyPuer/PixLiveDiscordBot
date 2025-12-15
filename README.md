# PixLive Discord & Telegram Bot

Async Discord bot that posts new DeviantArt posts to a specified channel, with an administrative Telegram bot (password-protected) for control and analytics. Config is read from `.env`.

Quickstart
- copy `.env.example` to `.env` and fill tokens
- set `DEVIANTART_USERNAMES` in `.env` to a comma-separated list (e.g. `artist1,artist2`)
- install deps: `pip install -r requirements.txt`
- run: `python main.py`

Features
- Poll DeviantArt RSS feeds and post new deviations to Discord
- Extensible services architecture (add more services)
- Telegram admin bot with password-based auth for controlling services and viewing analytics
