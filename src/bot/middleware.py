"""
Authentication middleware for the bot
"""
from telegram import Update
from telegram.ext import ContextTypes
from functools import wraps
from src.database.models import Database
import logging

db = Database()
logger = logging.getLogger(__name__)


def require_auth(func):
    """
    Decorator to require authentication for handler functions
    Automatically detects if it's a callback query or message and applies appropriate protections

    Usage:
        @require_auth
        async def my_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            # Your handler code
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        telegram_id = user.id

        # Detect if this is a callback query or message
        is_callback = update.callback_query is not None

        if is_callback:
            # CALLBACK QUERY HANDLING with 4-layer duplicate prevention
            query = update.callback_query
            query_id = query.id

            # Initialize bot_data storage if not exists
            if 'processed_queries' not in context.bot_data:
                context.bot_data['processed_queries'] = set()

            # LAYER 1: Check if we've already processed this exact query ID globally
            if query_id in context.bot_data['processed_queries']:
                logger.debug(f"Duplicate query detected and ignored: {query_id}")
                return  # Skip duplicate queries

            # Mark this query as processed immediately (before any async work)
            context.bot_data['processed_queries'].add(query_id)

            # Keep only last 100 query IDs to prevent memory growth
            if len(context.bot_data['processed_queries']) > 100:
                queries_list = list(context.bot_data['processed_queries'])
                context.bot_data['processed_queries'] = set(queries_list[-100:])

            # LAYER 2: Prevent duplicate processing by checking processing state
            if context.user_data.get('processing'):
                logger.debug(f"User {telegram_id} already processing a request")
                return  # Silently ignore if already processing

            # Set processing state immediately to prevent race conditions
            context.user_data['processing'] = True

            try:
                # Check if user is authorized
                if not db.is_user_authorized(telegram_id):
                    await query.answer("⛔ You are not authorized to use this bot.")
                    return

                # Update user info if needed
                db.update_user_info(telegram_id, user.username, user.full_name)

                # LAYER 3: Answer the callback query immediately (unless handler does it)
                # We'll answer it here to prevent loading indicators during rapid taps
                try:
                    await query.answer()
                except:
                    pass  # Handler might have already answered

                # LAYER 4: Call the original handler
                return await func(update, context, *args, **kwargs)

            except Exception as e:
                logger.error(f"Error in callback handler: {e}", exc_info=True)
                try:
                    await query.answer("❌ An error occurred. Please try again.")
                except:
                    pass
                raise

            finally:
                # Always clear processing state (guaranteed cleanup)
                context.user_data.pop('processing', None)

        else:
            # MESSAGE HANDLING (original behavior)
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
    Includes 4-layer duplicate prevention system to prevent double-click issues

    Usage:
        @require_auth_callback
        async def my_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
            # Your callback code
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        query = update.callback_query
        user = update.effective_user
        telegram_id = user.id
        query_id = query.id

        # Initialize bot_data storage if not exists
        if 'processed_queries' not in context.bot_data:
            context.bot_data['processed_queries'] = set()

        # LAYER 1: Check if we've already processed this exact query ID globally
        if query_id in context.bot_data['processed_queries']:
            logger.debug(f"Duplicate query detected and ignored: {query_id}")
            return  # Skip duplicate queries

        # Mark this query as processed immediately (before any async work)
        context.bot_data['processed_queries'].add(query_id)

        # Keep only last 100 query IDs to prevent memory growth
        if len(context.bot_data['processed_queries']) > 100:
            # Remove oldest items (since sets are unordered, we convert to list and slice)
            queries_list = list(context.bot_data['processed_queries'])
            context.bot_data['processed_queries'] = set(queries_list[-100:])

        # LAYER 2: Prevent duplicate processing by checking processing state
        if context.user_data.get('processing'):
            logger.debug(f"User {telegram_id} already processing a request")
            return  # Silently ignore if already processing

        # Set processing state immediately to prevent race conditions
        context.user_data['processing'] = True

        try:
            # Check if user is authorized
            if not db.is_user_authorized(telegram_id):
                await query.answer("⛔ You are not authorized to use this bot.")
                return

            # Update user info if needed
            db.update_user_info(telegram_id, user.username, user.full_name)

            # LAYER 3: Answer the callback query immediately to prevent loading indicators
            await query.answer()

            # LAYER 4: Call the original handler
            return await func(update, context, *args, **kwargs)

        except Exception as e:
            logger.error(f"Error in callback handler: {e}", exc_info=True)
            try:
                await query.answer("❌ An error occurred. Please try again.")
            except:
                pass
            raise

        finally:
            # Always clear processing state (guaranteed cleanup)
            context.user_data.pop('processing', None)

    return wrapper
