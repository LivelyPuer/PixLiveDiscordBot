import asyncio
import logging
import discord
from bot.config import cfg
from bot.discord_admin import DiscordAdmin
from bot.discord_logger import DiscordLogHandler


logger = logging.getLogger(__name__)


class DiscordPoster:
    def __init__(self, services, state, service_manager, telegram_service=None):
        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = discord.Client(intents=intents)
        self.services = services
        self.telegram_service = telegram_service
        self.state = state
        self.service_manager = service_manager
        self._bot_ready = asyncio.Event()
        self.admin = None
        self.posts_channel = None


        @self.bot.event
        async def on_ready():
            logger.info(f"✅ Discord client ready as {self.bot.user}")
            # Initialize admin and posts channel on first ready
            if self.admin is None:
                self.admin = DiscordAdmin(self.bot, self.state, self.service_manager)
                await self.admin.initialize()
                
                # Attach Discord logger handler after admin is ready
                if self.admin.logs_channel:
                    discord_handler = DiscordLogHandler(self.admin)
                    discord_handler.setLevel(logging.ERROR)  # Only send ERROR and CRITICAL logs to Discord
                    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                    discord_handler.setFormatter(formatter)
                    logging.getLogger().addHandler(discord_handler)
                    logger.info("✅ Discord logging enabled")
            
            if self.posts_channel is None:
                await self._initialize_posts_channel()
            

            
            self._bot_ready.set()
        
        @self.bot.event
        async def on_error(event, *args, **kwargs):
            logger.error(f"Discord event error in {event}: {args}, {kwargs}", exc_info=True)

    async def _get_channel_by_name(self, name: str):
        """Find a channel by name across all guilds."""
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                if channel.name == name:
                    return channel
        return None

    async def _initialize_posts_channel(self):
        """Find posts channel by name across all guilds."""
        self.posts_channel = await self._get_channel_by_name(cfg.discord_posts_channel_name)
        if self.posts_channel:
            logger.info(f"✅ Posts channel found: #{self.posts_channel.name}")
        else:
            logger.error(f"❌ Posts channel not found: {cfg.discord_posts_channel_name}")

    async def on_telegram_post(self, payload: dict):
        """Callback for Telegram service to post to Discord."""
        await self._bot_ready.wait()
        
        try:
            target_channel_name = payload.get("target_channel_name")
            
            # Find target channel
            channel = None
            if target_channel_name:
                channel = await self._get_channel_by_name(target_channel_name)
            
            if not channel:
                channel = self.posts_channel
                if channel:
                    logger.warning(f"Target channel {target_channel_name} not found, using default {channel.name}")
            
            if not channel:
                logger.error("No channel available to post message")
                return

            source = payload.get("source")
            title = payload.get("title", "New Post")
            url = payload.get("url", "")
            
            # Check if this is a collection (batch) or single announcement
            if source == "telegram_collection":
                # Collections Flow
                files_data = payload.get("files", []) # List of (filename, bytes)
                description = payload.get("description", "")
                
                # Create Discord Files
                discord_files = []
                import io
                for fname, fbytes in files_data:
                    discord_files.append(discord.File(io.BytesIO(fbytes), filename=fname))
                
                # Generate Random Bright Color
                import random
                import colorsys
                
                # HSV: Hue random (0-1), Saturation high (0.7-1.0), Value high (0.8-1.0)
                h = random.random()
                s = 0.7 + random.random() * 0.3
                v = 0.8 + random.random() * 0.2
                r, g, b = colorsys.hsv_to_rgb(h, s, v)
                r, g, b = int(r*255), int(g*255), int(b*255)
                bright_color = discord.Color.from_rgb(r, g, b)
                
                embed = discord.Embed(
                    description=description,
                    color=bright_color
                )

                # Send message with embed (Text)
                await channel.send(embed=embed)
                
                # Send files (Images) in batches
                for i in range(0, len(discord_files), 10):
                    await channel.send(files=discord_files[i:i+10])

                logger.info(f"📤 Sent Collection to Discord #{channel.name}")
                
            else:
                # Announcement Flow (Single Image Embed)
                image_bytes = payload.get("image_bytes")
                filename = payload.get("filename", "image.jpg")
                
                embed = discord.Embed(
                    title=title,
                    url=url,
                    description="✨ **New Exclusive Post on Patreon!** ✨",
                    color=0xFF424D # Patreon Brand Color
                )
                
                file = None
                if image_bytes:
                    import io
                    file = discord.File(io.BytesIO(image_bytes), filename=filename)
                    embed.set_image(url=f"attachment://{filename}")
                
                await channel.send(embed=embed, file=file)
                logger.info(f"📤 Sent Announcement to Discord #{channel.name}")
            
            # increment analytics
            await self.state.update("analytics:posts_sent", lambda v: (v or 0) + 1)
            
        except Exception as e:
            logger.error(f"💥 Error processing Telegram post: {e}", exc_info=True)

    async def start(self):
        """Start Discord bot and services concurrently."""
        # Start Discord bot in background task
        bot_task = asyncio.create_task(self.bot.start(cfg.discord_token))
        
        try:
            logger.info("Attempting to connect to Discord...")
            
            # Wait for bot to be ready (increased timeout to 60 seconds)
            ready_task = asyncio.create_task(self._bot_ready.wait())
            
            # Race between bot_task and ready event with timeout
            done, pending = await asyncio.wait(
                [bot_task, ready_task],
                timeout=60,
                return_when=asyncio.FIRST_EXCEPTION
            )
            
            # Check if bot_task failed
            if bot_task in done:
                try:
                    bot_task.result()
                except Exception as e:
                    logger.error(f"Discord bot connection failed: {e}", exc_info=True)
                    await self.bot.close()
                    raise
            
            # Check if ready event fired
            if not self._bot_ready.is_set():
                logger.error("Discord bot failed to connect within 60 seconds")
                await self.bot.close()
                if not bot_task.done():
                    bot_task.cancel()
                raise TimeoutError("Discord bot did not become ready within 60 seconds")
            
            logger.info("Discord bot connected, starting services")
            
            # Start service polling tasks
            service_tasks = [
                asyncio.create_task(self._run_service(s)) for s in self.services
            ]
            
            if self.telegram_service:
                service_tasks.append(asyncio.create_task(self.telegram_service.start()))
            
            # Wait for bot or services to fail
            await asyncio.gather(bot_task, *service_tasks)
        except asyncio.CancelledError:
            logger.info("Discord bot startup cancelled")
            await self.bot.close()
            raise
        except Exception as e:
            logger.error(f"Unexpected error in Discord bot: {e}", exc_info=True)
            await self.bot.close()
            raise


    async def _run_service(self, service):
        """Run a single service with polling."""
        async def getter(k):
            return await self.state.get(k, None)

        async def setter(k, v):
            await self.state.set(k, v)

        # Use standard handler for all services
        await self._run_standard_service(service, getter, setter)

    async def _run_standard_service(self, service, getter, setter):
        """Run a standard service (DeviantArt, etc) with polling."""
        async def on_new(service_obj, deviation):
            # Extract data from DeviantArt API deviation object
            try:
                title = deviation.get("title", "No title")
                url = deviation.get("url", "#")
                thumbs = deviation.get("thumbs", [])
                
                # Check if post already sent
                sent_posts = await self.state.get("sent_posts", [])
                if url in sent_posts:
                    logger.info(f"⏭️ Skipping duplicate post: {title} ({url})")
                    return
                
                # thumbs is a list of dicts with 'src', 'height', 'width'
                thumb_url = None
                if thumbs:
                    thumb_obj = thumbs[0]
                    if isinstance(thumb_obj, dict):
                        thumb_url = thumb_obj.get("src")
                    else:
                        thumb_url = str(thumb_obj)
                
                # Wait for bot to be ready
                await self._bot_ready.wait()
                
                # send message to channel
                channel = self.posts_channel
                if channel is None:
                    logger.error(f"Posts channel not available: {cfg.discord_posts_channel_name}")
                    return
                
                # Get embed style
                embed_style = await self.state.get("embed_style", "full")
                
                # Build message based on style
                if embed_style == "text":
                    # Simple text message
                    await channel.send(f"**{title}**\n{url}")
                elif embed_style == "compact":
                    # Minimal embed
                    embed = discord.Embed(
                        title=title,
                        url=url,
                        color=discord.Color.blue()
                    )
                    if thumb_url:
                        embed.set_image(url=thumb_url)
                    await channel.send(embed=embed)
                else:  # "full" style (default)
                    # Full embed with description
                    embed = discord.Embed(
                        title=title,
                        url=url,
                        description=f"New post from {service_obj.username}",
                        color=discord.Color.blue()
                    )
                    if thumb_url:
                        embed.set_image(url=thumb_url)
                    await channel.send(embed=embed)
                logger.info(f"📤 Posted to Discord: {title} by {service_obj.username}")
                
                # Add to sent posts
                sent_posts.append(url)
                await self.state.set("sent_posts", sent_posts)
                
                # increment analytics
                await self.state.update("analytics:posts_sent", lambda v: (v or 0) + 1)
            except Exception as e:
                logger.error(f"💥 Error posting to Discord: {e}", exc_info=True)

        await service.start(getter, setter, on_new)
