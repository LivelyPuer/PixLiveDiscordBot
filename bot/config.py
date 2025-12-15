import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    discord_token: str = os.getenv("DISCORD_TOKEN", "")
    discord_channel_id: int = int(os.getenv("DISCORD_CHANNEL_ID", "0"))
    tg_bot_token: str = os.getenv("TG_BOT_TOKEN", "")
    tg_admin_password: str = os.getenv("TG_ADMIN_PASSWORD", "")
    poll_interval_seconds: int = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))
    state_file: str = os.getenv("STATE_FILE", "data/state.json")
    deviantart_client_id: str = os.getenv("DEVIANTART_CLIENT_ID", "")
    deviantart_client_secret: str = os.getenv("DEVIANTART_CLIENT_SECRET", "")
    deviantart_usernames: str = os.getenv("DEVIANTART_USERNAMES", "")


cfg = Config()
