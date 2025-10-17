"""
Authentication middleware for the bot
"""
from telegram import Update
from telegram.ext import ContextTypes
from functools import wraps
from src.database.models import Database


db = Database()


def require_auth(func):
    """
    Decorator to require authentication for handler functions

    Usage:
        @require_auth
        async def my_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            # Your handler code
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        telegram_id = user.id

        # Check if user is authorized
        if not db.is_user_authorized(telegram_id):
            await update.message.reply_text(
                "⛔ You are not authorized to use this bot.\n\n"
                "Please contact the administrator to get access."
            )
            return

        # Update user info if needed
        db.update_user_info(telegram_id, user.username, user.full_name)

        # Call the original handler
        return await func(update, context, *args, **kwargs)

    return wrapper


def require_auth_callback(func):
    """
    Decorator to require authentication for callback query handlers

    Usage:
        @require_auth_callback
        async def my_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
            # Your callback code
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        telegram_id = user.id

        # Check if user is authorized
        if not db.is_user_authorized(telegram_id):
            await update.callback_query.answer("⛔ You are not authorized to use this bot.")
            return

        # Update user info if needed
        db.update_user_info(telegram_id, user.username, user.full_name)

        # Call the original handler
        return await func(update, context, *args, **kwargs)

    return wrapper
