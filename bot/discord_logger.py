import asyncio
import logging
from queue import Queue


class DiscordLogHandler(logging.Handler):
    """Custom logging handler that sends logs to Discord."""
    
    def __init__(self, admin):
        super().__init__()
        self.admin = admin
        self.queue = Queue()
        self.loop = None
    
    def emit(self, record):
        """Emit a log record to Discord."""
        try:
            # Skip very verbose logs
            if record.levelno < logging.INFO:
                return
            
            # Format the message
            msg = self.format(record)
            
            # Skip certain noisy loggers
            if "discord.http" in record.name:
                return
            if "discord.gateway" in record.name and record.levelno < logging.WARNING:
                return
            
            # Get level based emoji and color
            level_map = {
                logging.DEBUG: ("🔍", "INFO"),
                logging.INFO: ("ℹ️", "INFO"),
                logging.WARNING: ("⚠️", "WARNING"),
                logging.ERROR: ("❌", "ERROR"),
                logging.CRITICAL: ("🔴", "ERROR"),
            }
            emoji, color = level_map.get(record.levelno, ("📝", "INFO"))
            
            # Create formatted message
            discord_msg = f"{emoji} **{record.name}**\n```\n{msg}\n```"
            
            # Queue the message
            self.queue.put((discord_msg, color))
            
            # Schedule sending if we have event loop
            if self.admin and self.admin.logs_channel:
                try:
                    asyncio.create_task(self._send_queued())
                except RuntimeError:
                    # No event loop running
                    pass
        except Exception as e:
            self.handleError(record)
    
    async def _send_queued(self):
        """Send queued messages to Discord."""
        while not self.queue.empty():
            try:
                msg, color = self.queue.get_nowait()
                await self.admin.log_to_channel(msg, color)
                await asyncio.sleep(0.5)  # Rate limiting
            except Exception as e:
                print(f"Error sending log to Discord: {e}")
                break
