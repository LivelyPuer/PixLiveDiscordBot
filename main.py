import asyncio
import logging
from bot.config import cfg
from bot.state import StateStore
from services.deviantart.service import DeviantArtService
from discord_bot import DiscordPoster
from telegram_admin import TelegramAdmin
from service_manager import ServiceManager


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    state = StateStore(cfg.state_file)
    svc_mgr = ServiceManager()

    # Validate Discord config
    if not cfg.discord_token:
        logger.error("❌ DISCORD_TOKEN not set in .env")
        return
    if not cfg.discord_channel_id or cfg.discord_channel_id == 0:
        logger.error("❌ DISCORD_CHANNEL_ID not set in .env")
        return

    # Validate Telegram config
    if not cfg.tg_bot_token:
        logger.error("❌ TG_BOT_TOKEN not set in .env")
        return
    if not cfg.tg_admin_password:
        logger.error("❌ TG_ADMIN_PASSWORD not set in .env")
        return

    # Validate DeviantArt config
    if not cfg.deviantart_client_id or not cfg.deviantart_client_secret:
        logger.error("❌ DEVIANTART_CLIENT_ID or DEVIANTART_CLIENT_SECRET not set in .env")
        return

    # Parse DeviantArt usernames from config
    usernames = [u.strip() for u in cfg.deviantart_usernames.split(",") if u.strip()]
    
    if not usernames:
        logger.error("❌ DEVIANTART_USERNAMES not configured. Set in .env (e.g., artist1,artist2)")
        return
    
    logger.info(f"✅ Configuration valid")
    logger.info(f"📊 Tracking {len(usernames)} artists: {', '.join(usernames)}")
    
    # Initialize DeviantArt services for each username
    services = []
    for username in usernames:
        da = DeviantArtService(
            username,
            client_id=cfg.deviantart_client_id,
            client_secret=cfg.deviantart_client_secret,
            poll_interval=cfg.poll_interval_seconds
        )
        services.append(da)
        svc_mgr.register(f"deviantart:{username}", da)
        logger.info(f"  → DeviantArt service for: {username}")

    discord_poster = DiscordPoster(services, state)
    telegram = TelegramAdmin(state, svc_mgr)

    logger.info("🚀 Starting Discord and Telegram bots...")
    
    # run discord and telegram concurrently
    try:
        await asyncio.gather(
            discord_poster.start(),
            telegram.start()
        )
    except KeyboardInterrupt:
        logger.info("⏹️ Shutting down...")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
