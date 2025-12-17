import asyncio
import logging
from bot.config import cfg
from bot.state import StateStore
from services.deviantart.service import DeviantArtService
from services.deviantart.service import DeviantArtService
from bot.discord_bot import DiscordPoster
from services.service_manager import ServiceManager
from services.telegram.service import TelegramService


logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def main():
    state = StateStore(cfg.state_file)
    svc_mgr = ServiceManager()

    # Validate Discord config
    if not cfg.discord_token:
        logger.error("❌ DISCORD_TOKEN not set in .env")
        return
    if not cfg.discord_posts_channel_name:
        logger.error("❌ DISCORD_POSTS_CHANNEL_NAME not set in .env")
        return
    if not cfg.discord_admin_password:
        logger.error("❌ DISCORD_ADMIN_PASSWORD not set in .env")
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
        logger.info(f"  → DeviantArt service initialized for: {username}")

    # Initialize Telegram Service
    discord_poster_ref = {}
    async def tg_callback(payload):
        if "poster" in discord_poster_ref:
            await discord_poster_ref["poster"].on_telegram_post(payload)
        else:
            logger.warning("DiscordPoster not ready to receive Telegram post")

    telegram_service = TelegramService(tg_callback)
    svc_mgr.register("telegram", telegram_service)
    logger.info("  → Telegram service initialized")

    discord_poster = DiscordPoster(services, state, svc_mgr, telegram_service=telegram_service)
    discord_poster_ref["poster"] = discord_poster

    logger.info("🚀 Starting Discord bot...")
    logger.info(f"📝 Posts channel: {cfg.discord_posts_channel_name}")
    logger.info(f"📋 Admin channel: {cfg.discord_admin_channel_name}")
    logger.info(f"⏱️  Poll interval: {cfg.poll_interval_seconds}s")
    
    # run discord concurrently with services
    
    # run discord concurrently with services
    try:
        await asyncio.gather(
            discord_poster.start()
        )
    except KeyboardInterrupt:
        logger.info("⏹️ Shutting down...")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️  Shutting down...")
    except TimeoutError as e:
        logger.error(f"❌ Connection timeout: {e}")
        logger.error("💡 Troubleshooting tips:")
        logger.error("   1. Check your DISCORD_TOKEN is valid")
        logger.error("   2. Verify network connectivity")
        logger.error("   3. Check Discord service status")
        logger.error("   4. Try increasing DISCORD_CONNECT_TIMEOUT if needed")
        exit(1)
    except Exception as e:
        logger.error(f"❌ Unrecoverable error: {e}", exc_info=True)
        exit(1)
