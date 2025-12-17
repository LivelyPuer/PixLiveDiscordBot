import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    discord_token: str = os.getenv("DISCORD_TOKEN", "")
    discord_posts_channel_name: str = os.getenv("DISCORD_POSTS_CHANNEL_NAME", "posts")
    discord_commands_channel_name: str = os.getenv("DISCORD_COMMANDS_CHANNEL_NAME", "admin-commands")
    discord_admin_channel_name: str = os.getenv("DISCORD_ADMIN_CHANNEL_NAME", "admin-logs")
    discord_admin_password: str = os.getenv("DISCORD_ADMIN_PASSWORD", "")
    poll_interval_seconds: int = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))
    state_file: str = os.getenv("STATE_FILE", "data/state.json")
    deviantart_client_id: str = os.getenv("DEVIANTART_CLIENT_ID", "")
    deviantart_client_secret: str = os.getenv("DEVIANTART_CLIENT_SECRET", "")
    deviantart_usernames: str = os.getenv("DEVIANTART_USERNAMES", "")
    
    # Telegram
    tg_bot_token: str = os.getenv("TG_BOT_TOKEN", "")
    tg_source_channel_id: str = os.getenv("TG_SOURCE_CHANNEL_ID", "")

    # Patreon
    patreon_access_token: str = os.getenv("PATREON_ACCESS_TOKEN", "")
    
    # Patreon Mappings
    patreon_channel: str = os.getenv("PATREON_CHANNEL", "announcement")
    patreon_sfw_channel: str = os.getenv("PATREON_SFW_CHANNEL", "sfw-announcement")
    patreon_nsfw_channel: str = os.getenv("PATREON_NSFW_CHANNEL", "nsfw-announcement")
    patreon_futa_channel: str = os.getenv("PATREON_FUTA_CHANNEL", "futa-announcement")
    patreon_limited_channel: str = os.getenv("PATREON_LIMITED_CHANNEL", "limited-announcement")

    # Collections Mappings
    patreon_sfw_col_channel: str = os.getenv("PATREON_SFW_COL_CHANNEL", "sfw-collections")
    patreon_nsfw_col_channel: str = os.getenv("PATREON_NSFW_COL_CHANNEL", "nsfw-collections")
    patreon_futa_col_channel: str = os.getenv("PATREON_FUTA_COL_CHANNEL", "futa-collections")
    patreon_limited_sfw_col_channel: str = os.getenv("PATREON_LIMITED_SFW_COL_CHANNEL", "limited-collections-sfw")
    patreon_limited_nsfw_col_channel: str = os.getenv("PATREON_LIMITED_NSFW_COL_CHANNEL", "limited-collections-nsfw")
    patreon_limited_futa_col_channel: str = os.getenv("PATREON_LIMITED_FUTA_COL_CHANNEL", "limited-collections-futa")


cfg = Config()
