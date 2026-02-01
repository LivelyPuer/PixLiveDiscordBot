import logging
import asyncio
import re
import os
from telegram import Update
from telegram.ext import Application, ApplicationBuilder, ContextTypes, MessageHandler, filters
from telegram.request import HTTPXRequest
from bot.config import cfg
from services.patreon.client import PatreonClient
from utils.image import blur_image


logger = logging.getLogger(__name__)


class TelegramService:
    def __init__(self, discord_poster_callback):
        self.callback = discord_poster_callback
        self.patreon = PatreonClient(cfg.patreon_access_token)
        self.app: Application = None
        self._running = False
        self.channel_mappings = {
            "sfw": cfg.patreon_sfw_channel,
            "nsfw": cfg.patreon_nsfw_channel,
            "futa": cfg.patreon_futa_channel,
            "limited": cfg.patreon_limited_channel
        }
        
        # Collections Mappings
        self.col_mappings = {
            "sfw": cfg.patreon_sfw_col_channel,
            "nsfw": cfg.patreon_nsfw_col_channel,
            "futa": cfg.patreon_futa_col_channel,
            "limited_sfw": cfg.patreon_limited_sfw_col_channel,
            "limited_nsfw": cfg.patreon_limited_nsfw_col_channel,
            "limited_futa": cfg.patreon_limited_futa_col_channel
        }
        
        # Fallback channel
        self.default_channel = cfg.patreon_channel

        # Regex to find Patreon URLs
        self.patreon_url_regex = re.compile(r"https?://(?:www\.)?patreon\.com/posts/(?:[\w-]+-)?(\d+)")
        
        # Album buffering
        self.album_buffer = {} # media_group_id -> [messages]
        self.album_tasks = {} # media_group_id -> asyncio.Task


    async def start(self):
        if not cfg.tg_bot_token:
            logger.error("TG_BOT_TOKEN not set. TelegramService not starting.")
            return

        # Читаем прокси из переменной окружения
        proxy_url = os.getenv("PROXY_URL")
        
        if proxy_url:
            logger.info(f"✓ Telegram: using proxy")
            
            # Создаём HTTPXRequest с прокси
            request = HTTPXRequest(
                proxy_url=proxy_url,
                connection_pool_size=8,
                connect_timeout=30.0,
                read_timeout=30.0,
                write_timeout=30.0,
                pool_timeout=30.0
            )
            
            # Создаём Application с прокси
            self.app = (
                ApplicationBuilder()
                .token(cfg.tg_bot_token)
                .request(request)
                .get_updates_request(request)
                .build()
            )
        else:
            logger.warning("⚠ Telegram: no proxy configured, direct connection")
            self.app = ApplicationBuilder().token(cfg.tg_bot_token).build()
        
        # Handle channel posts with photos
        self.app.add_handler(MessageHandler(filters.ChatType.CHANNEL & filters.PHOTO, self.handle_post))
        
        self._running = True
        logger.info("🚀 Starting Telegram Service...")
        
        await self.app.initialize()
        await self.app.start()
        
        await self.app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        
    async def stop(self):
        if self.app:
            logger.info("Stopping Telegram Service...")
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()


    async def handle_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = update.channel_post
        if not message:
            return

        # Check source channel if configured
        if cfg.tg_source_channel_id:
            if str(update.effective_chat.id) != str(cfg.tg_source_channel_id):
                return

        # Check for media group
        if message.media_group_id:
            gid = message.media_group_id
            if gid not in self.album_buffer:
                self.album_buffer[gid] = []
                # Schedule processing after delay
                self.album_tasks[gid] = asyncio.create_task(self._schedule_processing(gid))
            
            self.album_buffer[gid].append(message)
        else:
            # Single image - treat as group of 1 immediately (or with short delay to reuse logic?)
            # Reusing logic is simpler.
            gid = f"single_{message.message_id}"
            self.album_buffer[gid] = [message]
            await self.process_group(gid)


    async def _schedule_processing(self, group_id: str):
        await asyncio.sleep(4) # Wait 4 seconds for all images
        await self.process_group(group_id)
        # Cleanup
        if group_id in self.album_buffer:
            del self.album_buffer[group_id]
        if group_id in self.album_tasks:
            del self.album_tasks[group_id]


    async def process_group(self, group_id: str):
        if group_id not in self.album_buffer:
            return
            
        messages = self.album_buffer[group_id]
        if not messages:
            return
            
        # Sort messages by ID to keep order? Usually Telegram sends them in order.
        messages.sort(key=lambda m: m.message_id)
        
        # We need to find caption. Caption might be on one message or first one.
        # Check all messages for caption matching Patreon regex.
        caption = ""
        matched_message = None
        match = None
        
        for msg in messages:
            cap = msg.caption or ""
            m = self.patreon_url_regex.search(cap)
            if m:
                caption = cap
                match = m
                matched_message = msg
                break
        
        if not match:
            return # No Patreon URL found in group

        post_id = match.group(1)
        url = match.group(0)
        
        # Extract tags from the matched caption
        tags = [t.strip("#").lower() for t in caption.split() if t.startswith("#")]
        
        # Determine flags based on tags
        has_limited = "limited" in tags
        has_futa = "futa" in tags
        has_nsfw = "nsfw" in tags
        has_sfw = "sfw" in tags
        
        is_sensitive = has_limited or has_futa or has_nsfw

        # Fetch Title
        title = await self.patreon.get_post_title(post_id)
        if not title:
            title = "Patreon Publication"

        # --- FLOW 1: ANNOUNCEMENTS (Single Image, Blurred) ---
        # Take the first image (or the one with caption? User said "first image from group")
        # Let's take specific first message from sorted list
        first_msg = messages[0]
        first_photo = first_msg.photo[-1]
        file = await first_msg.get_bot().get_file(first_photo.file_id)
        first_image_bytes = await file.download_as_bytearray()
        
        # Announcement Targets
        ann_targets = []
        if has_limited:
            ann_targets.append((self.channel_mappings["limited"], True))
        if has_futa:
            ann_targets.append((self.channel_mappings["futa"], True))
        if has_nsfw:
            ann_targets.append((self.channel_mappings["nsfw"], True))
        if has_sfw:
            ann_targets.append((self.channel_mappings["sfw"], is_sensitive)) # Blur if sensitive tag present
            
        ann_targets.append((self.default_channel, is_sensitive))
        
        # Dedup Announcement Targets
        unique_ann_targets = {}
        for ch, blur in ann_targets:
            if not ch: continue
            if ch in unique_ann_targets:
                if blur: unique_ann_targets[ch] = True
            else:
                unique_ann_targets[ch] = blur
                
        # Send Announcements
        for ch_name, should_blur in unique_ann_targets.items():
            processed = first_image_bytes
            if should_blur:
                try:
                    processed = blur_image(bytes(first_image_bytes), radius=80)
                except Exception as e:
                    logger.error(f"Failed to blur: {e}")
                    processed = None
            
            if processed:
                payload = {
                    "source": "telegram",
                    "title": title,
                    "url": url,
                    "target_channel_name": ch_name,
                    "image_bytes": processed,
                    "filename": f"preview_{post_id}.jpg"
                }
                await self.callback(payload)
                logger.info(f"📢 Announcement: {post_id} -> #{ch_name}")

        # --- FLOW 2: COLLECTIONS (All Images, Unblurred) ---
        # Collect all images
        # We need to download all images. This might take time.
        # Max limit? Telegram albums are max 10 images.
        
        col_images = []
        for i, msg in enumerate(messages):
            try:
                p = msg.photo[-1]
                f = await msg.get_bot().get_file(p.file_id)
                b = await f.download_as_bytearray()
                col_images.append((f"img_{i}.jpg", b))
            except Exception as e:
                logger.error(f"Failed to download image {i} for collection: {e}")

        if not col_images:
            return

        # Collection Targets
        # Logic: 
        # sfw -> PATREON_SFW_COL_CHANNEL
        # nsfw -> PATREON_NSFW_COL_CHANNEL
        # futa -> PATREON_FUTA_COL_CHANNEL
        # limited + sfw -> PATREON_LIMITED_SFW_COL_CHANNEL
        # limited + nsfw -> PATREON_LIMITED_NSFW_COL_CHANNEL
        # limited + futa -> PATREON_LIMITED_FUTA_COL_CHANNEL
        
        col_targets = set()
        
        if has_limited:
            # Limited overrides normal categories
            if has_sfw: col_targets.add(self.col_mappings["limited_sfw"])
            if has_nsfw: col_targets.add(self.col_mappings["limited_nsfw"])
            if has_futa: col_targets.add(self.col_mappings["limited_futa"])
            # If limited but no sub-category? Fallback? Or maybe limited implies one of those?
            # User example: "sfw limited -> PATREON_LIMITED_SFW_COL_CHANNEL"
            # Assuming limited posts always have a sub-tag. If not, maybe skip?
        else:
            # Standard Collections
            if has_sfw: col_targets.add(self.col_mappings["sfw"])
            if has_nsfw: col_targets.add(self.col_mappings["nsfw"])
            if has_futa: col_targets.add(self.col_mappings["futa"])
            
        for ch_name in col_targets:
            if not ch_name: continue
            
            # Send Collection Payload
            # We need to send text + files
            # DiscordPoster needs update to handle 'files' list
            
            # Construct text content
            # "Title + URL + specific text from Patreon?"
            # User said "add text from patreon". We assume title + url? Or did we fetch body text?
            # API call `get_post_title` only fetched title.
            # I will add Title + URL to the payload logic.
            
            payload = {
                "source": "telegram_collection",
                "title": title,
                "url": url,
                "target_channel_name": ch_name,
                "files": col_images, # List of (filename, bytes)
                "description": f"✨ **New Collection Dropped!** ✨\n\n**{title}**\n\n🔥 **Check it out here:** <{url}>" 
            }
            
            await self.callback(payload)
            logger.info(f"📚 Collection: {post_id} -> #{ch_name} ({len(col_images)} images)")
