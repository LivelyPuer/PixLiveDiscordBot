import asyncio
import logging
import discord
from bot.config import cfg
from bot.discord_admin import DiscordAdmin


logger = logging.getLogger(__name__)


class DiscordPoster:
    def __init__(self, services, state, service_manager):
        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = discord.Client(intents=intents)
        self.services = services
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
            if self.posts_channel is None:
                await self._initialize_posts_channel()
            self._bot_ready.set()
        
        @self.bot.event
        async def on_error(event, *args, **kwargs):
            logger.error(f"Discord event error in {event}: {args}, {kwargs}", exc_info=True)

    async def _initialize_posts_channel(self):
        """Find posts channel by name across all guilds."""
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                if channel.name == cfg.discord_posts_channel_name:
                    self.posts_channel = channel
                    logger.info(f"✅ Posts channel found: #{channel.name} in {guild.name}")
                    return
        logger.error(f"❌ Posts channel not found: {cfg.discord_posts_channel_name}")
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

        async def on_new(service_obj, deviation):
            # Extract data from DeviantArt API deviation object
            try:
                title = deviation.get("title", "No title")
                url = deviation.get("url", "#")
                thumbs = deviation.get("thumbs", [])
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
                
                # Build embed message
                embed = discord.Embed(
                    title=title,
                    url=url,
                    description=f"New post from {service_obj.username}",
                    color=discord.Color.blue()
                )
                if thumb_url:
                    embed.set_image(url=thumb_url)
                
                await channel.send(embed=embed)
                logger.info(f"Posted: {title} by {service_obj.username}")
                
                # increment analytics
                await self.state.update("analytics:posts_sent", lambda v: (v or 0) + 1)
            except Exception as e:
                logger.error(f"Error posting to Discord: {e}", exc_info=True)

        await service.start(getter, setter, on_new)
