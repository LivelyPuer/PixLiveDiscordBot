import asyncio
import logging
import discord
from bot.config import cfg


logger = logging.getLogger(__name__)


class DiscordAdmin:
    def __init__(self, bot, state, service_manager):
        """Initialize Discord admin interface.
        
        Args:
            bot: discord.Client instance
            state: StateStore instance
            service_manager: ServiceManager instance
        """
        self.bot = bot
        self.state = state
        self.service_manager = service_manager
        self.commands_channel = None
        self.logs_channel = None
        self._authorized_users = set()
        
        # Register ready event for admin channel
        @self.bot.event
        async def on_message(message):
            try:
                if message.author == self.bot.user:
                    return
                
                logger.debug(f"Message from {message.author} in {message.channel}: {message.content}")
                
                # Only process in commands channel
                if self.commands_channel is None:
                    logger.debug(f"Commands channel not initialized yet")
                    return
                
                if message.channel.id != self.commands_channel.id:
                    return
                
                logger.info(f"Processing command from {message.author}: {message.content}")
                await self._process_command(message)
            except Exception as e:
                logger.error(f"Error in on_message: {e}", exc_info=True)
    
    async def initialize(self):
        """Initialize command and log channel references."""
        # Find channels by name
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                if channel.name == cfg.discord_commands_channel_name:
                    self.commands_channel = channel
                    logger.info(f"✅ Commands channel found: #{channel.name} in {guild.name}")
                
                if channel.name == cfg.discord_admin_channel_name:
                    self.logs_channel = channel
                    logger.info(f"✅ Logs channel found: #{channel.name} in {guild.name}")
                    
                    # Send startup notification
                    await self._send_startup_message()
        
        if self.commands_channel is None:
            logger.error(f"❌ Commands channel not found: {cfg.discord_commands_channel_name}")
        if self.logs_channel is None:
            logger.error(f"❌ Logs channel not found: {cfg.discord_admin_channel_name}")
    
    async def _send_startup_message(self):
        """Send startup notification with available commands."""
        if self.logs_channel is None:
            return
        
        embed = discord.Embed(
            title="🚀 PixLive Bot Started",
            description="Bot is online and ready to receive commands",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="📋 Available Commands",
            value="```\n"
                  "!auth <password>         - Authenticate\n"
                  "!status                  - Show bot status\n"
                  "!pause <service>         - Pause service\n"
                  "!resume <service>        - Resume service\n"
                  "!embed-style [style]     - Change post style\n"
                  "!help                    - Show all commands\n"
                  "```",
            inline=False
        )
        
        embed.add_field(
            name="💡 Quick Start",
            value="1. Use `!auth <password>` to authenticate\n"
                  "2. Use `!status` to see current status\n"
                  "3. Use `!help` for detailed information",
            inline=False
        )
        
        try:
            await self.logs_channel.send(embed=embed)
            logger.info("✅ Startup notification sent to logs channel")
        except Exception as e:
            logger.error(f"Failed to send startup message: {e}")
    
    async def _process_command(self, message):
        """Process admin commands from Discord."""
        content = message.content.strip()
        
        if not content.startswith("!"):
            return
        
        parts = content[1:].split()
        if not parts:
            return
        
        command = parts[0].lower()
        args = parts[1:]
        
        logger.info(f"Command: {command}, Args: {args}")
        
        try:
            if command == "auth":
                await self._auth(message, args)
            elif command == "status":
                await self._status(message, args)
            elif command == "pause":
                await self._pause(message, args)
            elif command == "resume":
                await self._resume(message, args)
            elif command == "embed-style":
                await self._embed_style(message, args)
            elif command == "poll-interval":
                await self._poll_interval(message, args)
            elif command == "help":
                await self._help(message)
            else:
                await message.reply("Unknown command. Use `!help` for available commands.")
        except Exception as e:
            logger.error(f"Error processing command: {e}", exc_info=True)
            await message.reply(f"Error: {e}")
    
    async def _auth(self, message, args):
        """Authenticate user with password."""
        if not args:
            await message.reply("Usage: `!auth <password>`")
            return
        
        password = args[0]
        if password == cfg.discord_admin_password:
            self._authorized_users.add(message.author.id)
            reply = await message.reply(f"✅ Authenticated! Welcome {message.author.mention}")
            logger.info(f"User {message.author} authenticated")
            
            # Delete original message with password
            try:
                await message.delete()
            except Exception as e:
                logger.error(f"Failed to delete auth message: {e}")
            
            # Delete bot reply after 5 seconds
            try:
                await asyncio.sleep(5)
                await reply.delete()
            except Exception as e:
                logger.error(f"Failed to delete reply: {e}")
        else:
            await message.reply("❌ Wrong password")
            
            # Delete original message with wrong password
            try:
                await message.delete()
            except Exception as e:
                logger.error(f"Failed to delete auth message: {e}")
    
    def _is_authorized(self, user_id):
        """Check if user is authorized."""
        return user_id in self._authorized_users
    
    async def _status(self, message, args):
        """Get bot status."""
        if not self._is_authorized(message.author.id):
            await message.reply("❌ Not authorized. Use `!auth <password>`")
            return
        
        analytics = await self.state.get("analytics:posts_sent", 0)
        posts_count = len(await self.state.get("sent_posts", []))
        embed_style = await self.state.get("embed_style", "full")
        poll_interval = await self.state.get("poll_interval_seconds", cfg.poll_interval_seconds)
        
        embed = discord.Embed(title="📊 Bot Status", color=discord.Color.green())
        embed.add_field(name="Posts Sent", value=str(analytics), inline=False)
        embed.add_field(name="Unique Posts Tracked", value=str(posts_count), inline=False)
        embed.add_field(name="Embed Style", value=f"**{embed_style}**", inline=False)
        embed.add_field(name="Poll Interval", value=f"**{poll_interval}** seconds", inline=False)
        embed.add_field(name="Connected", value="✅ Yes", inline=False)
        
        # Add service status
        status_text = "```\n"
        for service_name in self.service_manager.services:
            is_paused = self.service_manager.is_paused(service_name)
            status = "⏸ PAUSED" if is_paused else "▶ RUNNING"
            status_text += f"{service_name}: {status}\n"
        status_text += "```"
        embed.add_field(name="Services", value=status_text, inline=False)
        
        await message.reply(embed=embed)
    
    async def _pause(self, message, args):
        """Pause a service."""
        if not self._is_authorized(message.author.id):
            await message.reply("❌ Not authorized.")
            return
        
        if not args:
            await message.reply("Usage: `!pause <service_name>`")
            return
        
        service_name = args[0]
        ok = self.service_manager.pause(service_name)
        
        if ok:
            await message.reply(f"⏸ Paused: `{service_name}`")
            logger.info(f"Service paused: {service_name}")
        else:
            await message.reply(f"❌ Service not found: `{service_name}`")
    
    async def _resume(self, message, args):
        """Resume a service."""
        if not self._is_authorized(message.author.id):
            await message.reply("❌ Not authorized.")
            return
        
        if not args:
            await message.reply("Usage: `!resume <service_name>`")
            return
        
        service_name = args[0]
        ok = self.service_manager.resume(service_name)
        
        if ok:
            await message.reply(f"▶ Resumed: `{service_name}`")
            logger.info(f"Service resumed: {service_name}")
        else:
            await message.reply(f"❌ Service not found: `{service_name}`")
    
    async def _embed_style(self, message, args):
        """Change embed style for DeviantArt posts."""
        if not self._is_authorized(message.author.id):
            await message.reply("❌ Not authorized.")
            return
        
        if not args:
            current_style = await self.state.get("embed_style", "full")
            embed = discord.Embed(title="📋 Embed Style Settings", color=discord.Color.blue())
            embed.add_field(
                name="Current Style",
                value=f"**{current_style}**",
                inline=False
            )
            embed.add_field(
                name="Available Styles",
                value="```\nfull    - Embed with title, description, image\n"
                      "compact - Minimal embed with just title and image\n"
                      "text    - Simple text message (title + URL)\n```",
                inline=False
            )
            embed.add_field(
                name="Usage",
                value="`!embed-style <style_name>`",
                inline=False
            )
            await message.reply(embed=embed)
            return
        
        style = args[0].lower()
        if style not in ["full", "compact", "text"]:
            await message.reply(f"❌ Unknown style: `{style}`\nAvailable: full, compact, text")
            return
        
        await self.state.set("embed_style", style)
        await message.reply(f"✅ Embed style changed to: **{style}**")
        logger.info(f"Embed style changed to: {style}")
    
    async def _poll_interval(self, message, args):
        """Change DeviantArt polling interval."""
        if not self._is_authorized(message.author.id):
            await message.reply("❌ Not authorized.")
            return
        
        if not args:
            current_interval = await self.state.get("poll_interval_seconds", cfg.poll_interval_seconds)
            embed = discord.Embed(title="⏱️ Poll Interval Settings", color=discord.Color.blue())
            embed.add_field(
                name="Current Interval",
                value=f"**{current_interval}** seconds",
                inline=False
            )
            embed.add_field(
                name="Usage",
                value="`!poll-interval <seconds>`",
                inline=False
            )
            embed.add_field(
                name="Examples",
                value="```\n"
                      "!poll-interval 30    - Check every 30 seconds\n"
                      "!poll-interval 300   - Check every 5 minutes\n"
                      "!poll-interval 3600  - Check every hour\n"
                      "```",
                inline=False
            )
            await message.reply(embed=embed)
            return
        
        try:
            interval = int(args[0])
            if interval < 10:
                await message.reply("❌ Interval must be at least 10 seconds")
                return
            if interval > 86400:
                await message.reply("❌ Interval must be less than 24 hours (86400 seconds)")
                return
            
            await self.state.set("poll_interval_seconds", interval)
            await message.reply(f"✅ Poll interval changed to: **{interval}** seconds")
            logger.info(f"Poll interval changed to: {interval} seconds")
        except ValueError:
            await message.reply("❌ Invalid interval. Must be a number in seconds.")



    
    async def _help(self, message):
        """Show help message."""
        embed = discord.Embed(title="📖 Admin Commands", color=discord.Color.blue())
        embed.add_field(name="`!auth <password>`", value="Authenticate as admin", inline=False)
        embed.add_field(name="`!status`", value="Show bot status and analytics", inline=False)
        embed.add_field(name="`!pause <service_name>`", value="Pause a service", inline=False)
        embed.add_field(name="`!resume <service_name>`", value="Resume a service", inline=False)
        embed.add_field(name="`!embed-style [style]`", value="View/change DeviantArt post style\n(full/compact/text)", inline=False)
        embed.add_field(name="`!poll-interval [seconds]`", value="View/change DeviantArt check interval", inline=False)
        embed.add_field(name="`!help`", value="Show this help message", inline=False)
        await message.reply(embed=embed)
    
    async def log_to_channel(self, message: str, level: str = "INFO"):
        """Log a message to the logs channel."""
        if self.logs_channel is None:
            return
        
        # Color based on log level
        colors = {
            "INFO": discord.Color.blue(),
            "WARNING": discord.Color.gold(),
            "ERROR": discord.Color.red(),
            "SUCCESS": discord.Color.green()
        }
        
        color = colors.get(level, discord.Color.default())
        
        # Truncate long messages
        if len(message) > 2000:
            message = message[:1997] + "..."
        
        embed = discord.Embed(
            description=message,
            color=color
        )
        
        try:
            await self.logs_channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Failed to log to logs channel: {e}")
