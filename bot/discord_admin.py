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
        self.admin_channel = None
        self._authorized_users = set()
        
        # Register message handler
        @self.bot.event
        async def on_message(message):
            if message.author == self.bot.user:
                return
            
            # Only process in admin channel
            if self.admin_channel is None:
                return
            
            if message.channel.id != self.admin_channel.id:
                return
            
            await self._process_command(message)
    
    async def initialize(self):
        """Initialize admin channel reference."""
        # Find channel by name
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                if channel.name == cfg.discord_admin_channel_name:
                    self.admin_channel = channel
                    logger.info(f"✅ Admin channel found: #{channel.name} in {guild.name}")
                    return
        
        logger.error(f"❌ Admin channel not found: {cfg.discord_admin_channel_name}")
    
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
        
        try:
            if command == "auth":
                await self._auth(message, args)
            elif command == "status":
                await self._status(message, args)
            elif command == "pause":
                await self._pause(message, args)
            elif command == "resume":
                await self._resume(message, args)
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
            await message.reply(f"✅ Authenticated! Welcome {message.author.mention}")
            logger.info(f"User {message.author} authenticated")
        else:
            await message.reply("❌ Wrong password")
    
    def _is_authorized(self, user_id):
        """Check if user is authorized."""
        return user_id in self._authorized_users
    
    async def _status(self, message, args):
        """Get bot status."""
        if not self._is_authorized(message.author.id):
            await message.reply("❌ Not authorized. Use `!auth <password>`")
            return
        
        analytics = await self.state.get("analytics:posts_sent", 0)
        embed = discord.Embed(title="📊 Bot Status", color=discord.Color.green())
        embed.add_field(name="Posts Sent", value=str(analytics), inline=False)
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
    
    async def _help(self, message):
        """Show help message."""
        embed = discord.Embed(title="📖 Admin Commands", color=discord.Color.blue())
        embed.add_field(name="`!auth <password>`", value="Authenticate as admin", inline=False)
        embed.add_field(name="`!status`", value="Show bot status and analytics", inline=False)
        embed.add_field(name="`!pause <service_name>`", value="Pause a service", inline=False)
        embed.add_field(name="`!resume <service_name>`", value="Resume a service", inline=False)
        embed.add_field(name="`!help`", value="Show this help message", inline=False)
        await message.reply(embed=embed)
    
    async def log_to_channel(self, message: str, level: str = "INFO"):
        """Log a message to the admin channel."""
        if self.admin_channel is None:
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
            await self.admin_channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Failed to log to admin channel: {e}")
