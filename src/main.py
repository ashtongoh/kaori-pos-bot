"""
Main entry point for the Kori POS Bot
"""
import os
import logging
import asyncio
from dotenv import load_dotenv
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters
)

# Import handlers
from src.bot.handlers.control_panel import (
    start_command,
    control_panel_callback,
    view_past_sales_callback,
    view_past_inventory_callback
)
from src.bot.handlers.setup import (
    manage_menu_command,
    start_add_menu_item,
    cancel_menu_setup,
    delete_menu_item_callback,
    confirm_delete_menu_item_callback,
    edit_menu_item_callback,
    edit_name_callback,
    edit_size_callback,
    edit_price_callback,
    handle_has_sizes_callback,
    handle_add_more_sizes_callback
)
from src.bot.handlers.inventory import (
    start_session_callback,
    start_adding_inventory_callback,
    skip_inventory,
    cancel_session_start_callback,
    add_another_inventory_callback,
    skip_inventory_price_callback,
    handle_inventory_message
)
from src.bot.handlers.sales import (
    show_sales_dashboard,
    join_session_callback,
    refresh_dashboard_callback,
    new_order_callback,
    add_item_to_cart_callback,
    clear_cart_callback,
    confirm_cart_callback,
    payment_method_callback,
    cancel_order_callback,
    cancel_payment_callback,
    end_session_callback,
    confirm_end_session_callback,
    back_to_dashboard_callback
)
from src.bot.handlers.orders import (
    view_orders_callback,
    view_order_detail_callback,
    delete_order_callback,
    confirm_delete_order_callback
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get configuration from environment
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
PORT = int(os.getenv("PORT", 8443))
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Initialize Flask app for webhook (only used in production)
app = Flask(__name__)

# Initialize bot application
application = None


def setup_handlers(app: Application):
    """Setup all bot handlers"""

    # Command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("resume", start_command))  # /resume acts like /start

    # Menu setup handlers - Manual state management
    # Entry point for adding menu items
    app.add_handler(CallbackQueryHandler(start_add_menu_item, pattern="^add_menu_item$"))

    # Cancel handlers
    app.add_handler(CallbackQueryHandler(cancel_menu_setup, pattern="^cancel_menu_setup$"))
    app.add_handler(CommandHandler("cancel", cancel_menu_setup))

    # Message handler for menu item setup flow (checks context.user_data['menu_state'])
    from src.bot.handlers.setup import handle_menu_message
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_message), group=1)

    # Message handler for inventory flow (checks context.user_data['inventory_state'])
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_inventory_message), group=2)

    # Inventory session start handlers - Manual state management
    app.add_handler(CallbackQueryHandler(start_session_callback, pattern="^start_session$"))
    app.add_handler(CallbackQueryHandler(start_adding_inventory_callback, pattern="^start_adding_inventory$"))
    app.add_handler(CallbackQueryHandler(skip_inventory, pattern="^skip_inventory$"))
    app.add_handler(CallbackQueryHandler(cancel_session_start_callback, pattern="^cancel_session_start$"))
    app.add_handler(CallbackQueryHandler(add_another_inventory_callback, pattern="^add_another_inventory:"))
    app.add_handler(CallbackQueryHandler(skip_inventory_price_callback, pattern="^skip_inventory_price$"))

    # Control panel callbacks
    app.add_handler(CallbackQueryHandler(control_panel_callback, pattern="^control_panel$"))
    app.add_handler(CallbackQueryHandler(view_past_sales_callback, pattern="^view_sales"))
    app.add_handler(CallbackQueryHandler(view_past_inventory_callback, pattern="^view_inventory$"))

    # Menu management callbacks
    app.add_handler(CallbackQueryHandler(manage_menu_command, pattern="^manage_menu$"))
    app.add_handler(CallbackQueryHandler(edit_menu_item_callback, pattern="^edit_menu_item:"))
    app.add_handler(CallbackQueryHandler(edit_name_callback, pattern="^edit_name:"))
    app.add_handler(CallbackQueryHandler(edit_size_callback, pattern="^edit_size:"))
    app.add_handler(CallbackQueryHandler(edit_price_callback, pattern="^edit_price:"))
    app.add_handler(CallbackQueryHandler(confirm_delete_menu_item_callback, pattern="^confirm_delete_menu_item:"))
    app.add_handler(CallbackQueryHandler(delete_menu_item_callback, pattern="^delete_menu_item:"))
    app.add_handler(CallbackQueryHandler(handle_has_sizes_callback, pattern="^has_multiple_sizes:"))
    app.add_handler(CallbackQueryHandler(handle_add_more_sizes_callback, pattern="^add_more_sizes:"))

    # Sales dashboard callbacks
    app.add_handler(CallbackQueryHandler(join_session_callback, pattern="^join_session$"))
    app.add_handler(CallbackQueryHandler(refresh_dashboard_callback, pattern="^refresh_dashboard$"))
    app.add_handler(CallbackQueryHandler(new_order_callback, pattern="^new_order$"))
    app.add_handler(CallbackQueryHandler(add_item_to_cart_callback, pattern="^add_item:"))
    app.add_handler(CallbackQueryHandler(clear_cart_callback, pattern="^clear_cart$"))
    app.add_handler(CallbackQueryHandler(confirm_cart_callback, pattern="^confirm_cart$"))
    app.add_handler(CallbackQueryHandler(payment_method_callback, pattern="^payment:"))
    app.add_handler(CallbackQueryHandler(cancel_order_callback, pattern="^cancel_order$"))
    app.add_handler(CallbackQueryHandler(cancel_payment_callback, pattern="^cancel_payment$"))
    app.add_handler(CallbackQueryHandler(end_session_callback, pattern="^end_session$"))
    app.add_handler(CallbackQueryHandler(confirm_end_session_callback, pattern="^confirm_end_session$"))
    app.add_handler(CallbackQueryHandler(back_to_dashboard_callback, pattern="^back_to_dashboard$"))

    # Order management callbacks
    app.add_handler(CallbackQueryHandler(view_orders_callback, pattern="^view_orders$"))
    app.add_handler(CallbackQueryHandler(view_orders_callback, pattern="^orders_page:"))
    app.add_handler(CallbackQueryHandler(view_order_detail_callback, pattern="^view_order:"))
    app.add_handler(CallbackQueryHandler(delete_order_callback, pattern="^delete_order:"))
    app.add_handler(CallbackQueryHandler(confirm_delete_order_callback, pattern="^confirm_delete:"))

    logger.info("All handlers registered successfully")


@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    """Handle incoming webhook requests"""
    if request.method == "POST":
        update_data = request.get_json(force=True)

        # Process the update synchronously using asyncio.run
        try:
            async def process_update():
                update = Update.de_json(update_data, application.bot)
                await application.process_update(update)

            # Get or create event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is already running, create a new one
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Run the async function
            loop.run_until_complete(process_update())

            return "OK", 200
        except Exception as e:
            logger.error(f"Error processing webhook: {e}", exc_info=True)
            return "Error", 500

    return "Method not allowed", 405


@app.route("/")
def index():
    """Health check endpoint"""
    return "Kori POS Bot is running!"


async def setup_webhook():
    """Setup webhook for the bot"""
    webhook_url = f"{WEBHOOK_URL}/{BOT_TOKEN}"
    await application.bot.set_webhook(webhook_url)
    logger.info(f"Webhook set to: {webhook_url}")


def init_bot():
    """Initialize bot application for webhook mode"""
    global application

    if application is None:
        logger.info("Initializing bot application...")
        application = Application.builder().token(BOT_TOKEN).build()
        setup_handlers(application)

        # Initialize the application synchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(application.initialize())
        loop.run_until_complete(setup_webhook())
        logger.info("Bot application initialized successfully")

    return application


def main():
    """Main function to run the bot"""
    global application

    # Create application
    application = Application.builder().token(BOT_TOKEN).build()

    # Setup handlers
    setup_handlers(application)

    # Run based on environment
    if ENVIRONMENT == "production" and WEBHOOK_URL:
        # Production mode: Use webhook with Gunicorn
        logger.info("Running in PRODUCTION mode with webhook")
        logger.info("Use Gunicorn to run this application")
        # Initialization will happen when Gunicorn starts
    else:
        # Development mode: Use polling
        logger.info("Running in DEVELOPMENT mode with polling")
        logger.info("Bot is now running. Press Ctrl+C to stop.")

        # Run with polling
        application.run_polling(allowed_updates=Update.ALL_TYPES)


# Initialize bot when module is loaded (for Gunicorn)
if ENVIRONMENT == "production" and WEBHOOK_URL:
    init_bot()


if __name__ == "__main__":
    main()
