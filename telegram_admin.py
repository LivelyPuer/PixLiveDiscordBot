import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from bot.config import cfg


class TelegramAdmin:
    def __init__(self, state, service_manager):
        self.state = state
        self.service_manager = service_manager
        self.app = ApplicationBuilder().token(cfg.tg_bot_token).build()
        self.app.add_handler(CommandHandler("auth", self.auth))
        self.app.add_handler(CommandHandler("status", self.status))
        self.app.add_handler(CommandHandler("pause", self.pause))
        self.app.add_handler(CommandHandler("resume", self.resume))

    async def auth(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        args = context.args
        if not args:
            await update.message.reply_text("Usage: /auth <password>")
            return
        pw = args[0]
        if pw == cfg.tg_admin_password:
            # store authorized user
            auth = await self.state.get("tg:auth_users", [])
            if update.effective_user.id not in auth:
                auth.append(update.effective_user.id)
                await self.state.set("tg:auth_users", auth)
            await update.message.reply_text("Authenticated")
        else:
            await update.message.reply_text("Wrong password")

    async def _is_auth(self, user_id: int):
        auth = await self.state.get("tg:auth_users", [])
        return user_id in auth

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._is_auth(update.effective_user.id):
            await update.message.reply_text("Not authorized. Use /auth <password>")
            return
        analytics = await self.state.get("analytics:posts_sent", 0)
        await update.message.reply_text(f"Posts sent: {analytics}")

    async def pause(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._is_auth(update.effective_user.id):
            await update.message.reply_text("Not authorized.")
            return
        if not context.args:
            await update.message.reply_text("Usage: /pause <service_name>")
            return
        name = context.args[0]
        ok = self.service_manager.pause(name)
        await update.message.reply_text("Paused" if ok else "Service not found")

    async def resume(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._is_auth(update.effective_user.id):
            await update.message.reply_text("Not authorized.")
            return
        if not context.args:
            await update.message.reply_text("Usage: /resume <service_name>")
            return
        name = context.args[0]
        ok = self.service_manager.resume(name)
        await update.message.reply_text("Resumed" if ok else "Service not found")

    async def start(self):
        """Start Telegram bot polling in background."""
        try:
            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                timeout=30
            )
        except Exception as e:
            import logging
            logging.error(f"Telegram bot error: {e}", exc_info=True)
            raise
