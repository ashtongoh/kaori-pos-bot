"""
Menu setup handlers
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from src.bot.middleware import require_auth
from src.database.models import Database
from src.bot.keyboards import get_menu_management_keyboard, get_back_button, get_cancel_button, get_add_another_menu_item_keyboard
from src.utils.formatters import format_menu_list

db = Database()
logger = logging.getLogger(__name__)


@require_auth
async def manage_menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show menu management interface"""
    menu_items = db.get_menu_items()

    if not menu_items:
        text = "📋 *Menu Management*\n\nNo menu items found. Let's add your first item!"
        await update.callback_query.edit_message_text(text, parse_mode="Markdown")
        return await start_add_menu_item(update, context)

    text = f"📋 *Menu Management*\n\n{format_menu_list(menu_items)}\n\nSelect an item to edit or delete:"
    await update.callback_query.edit_message_text(
        text,
        reply_markup=get_menu_management_keyboard(menu_items),
        parse_mode="Markdown"
    )


@require_auth
async def start_add_menu_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the process of adding a new menu item"""
    logger.info(f"start_add_menu_item called by user {update.effective_user.id}")

    # Set state to expect menu name
    context.user_data['menu_state'] = 'MENU_NAME'
    context.user_data['new_menu_item'] = {}

    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text(
            "➕ *Add New Menu Item*\n\n"
            "Please enter the item name (e.g., 'Hojicha', 'Matcha'):\n\n"
            "Type /cancel to abort.",
            reply_markup=get_cancel_button(),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "➕ *Add New Menu Item*\n\n"
            "Please enter the item name (e.g., 'Hojicha', 'Matcha'):\n\n"
            "Type /cancel to abort.",
            reply_markup=get_cancel_button(),
            parse_mode="Markdown"
        )

    logger.info(f"Set menu_state to MENU_NAME")


async def receive_menu_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive the menu item name"""
    logger.info(f"receive_menu_name called by user {update.effective_user.id}")
    logger.info(f"Message text: {update.message.text}")

    name = update.message.text.strip()

    if not name:
        await update.message.reply_text(
            "❌ Item name cannot be empty. Please try again:",
            reply_markup=get_cancel_button()
        )
        return

    # Store in context
    context.user_data['new_menu_item']['name'] = name
    context.user_data['menu_state'] = 'MENU_SIZE'
    logger.info(f"Stored name in context: {name}, moving to MENU_SIZE state")

    await update.message.reply_text(
        f"✅ Item name: *{name}*\n\n"
        "Now enter the size (e.g., 'Reg', 'Large', 'Small'):",
        reply_markup=get_cancel_button(),
        parse_mode="Markdown"
    )


async def receive_menu_size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive the menu item size"""
    size = update.message.text.strip()

    if not size:
        await update.message.reply_text(
            "❌ Size cannot be empty. Please try again:",
            reply_markup=get_cancel_button()
        )
        return

    # Store in context
    context.user_data['new_menu_item']['size'] = size
    context.user_data['menu_state'] = 'MENU_PRICE'

    await update.message.reply_text(
        f"✅ Size: *{size}*\n\n"
        "Now enter the price (numbers only, e.g., '4.50'):",
        reply_markup=get_cancel_button(),
        parse_mode="Markdown"
    )


async def receive_menu_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive the menu item price and save"""
    price_text = update.message.text.strip()

    try:
        price = float(price_text)
        if price <= 0:
            raise ValueError("Price must be positive")
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid price. Please enter a valid number (e.g., '4.50'):",
            reply_markup=get_cancel_button()
        )
        return

    # Get item data from context
    item_data = context.user_data.get('new_menu_item', {})
    name = item_data.get('name')
    size = item_data.get('size')

    # Save to database
    result = db.add_menu_item(name, size, price)

    if result:
        await update.message.reply_text(
            f"✅ *Menu Item Added Successfully!*\n\n"
            f"*Name:* {name}\n"
            f"*Size:* {size}\n"
            f"*Price:* ${price:.2f}\n\n"
            "What would you like to do next?",
            reply_markup=get_add_another_menu_item_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "❌ Failed to add menu item. Please try again later.",
            reply_markup=get_back_button()
        )

    # Clear context
    context.user_data.pop('new_menu_item', None)
    context.user_data.pop('menu_state', None)


@require_auth
async def cancel_menu_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel menu item setup"""
    context.user_data.pop('new_menu_item', None)
    context.user_data.pop('menu_state', None)

    # Handle both callback query and message
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "❌ Menu item setup cancelled.",
            reply_markup=get_back_button()
        )
    else:
        await update.message.reply_text(
            "❌ Menu item setup cancelled.",
            reply_markup=get_back_button()
        )


@require_auth
async def delete_menu_item_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle menu item deletion"""
    query = update.callback_query
    await query.answer()

    # Extract item ID from callback data
    item_id = query.data.split(':')[1]

    # Delete the item
    success = db.delete_menu_item(item_id)

    if success:
        await query.edit_message_text(
            "✅ Menu item deleted successfully!",
            reply_markup=get_back_button()
        )
    else:
        await query.edit_message_text(
            "❌ Failed to delete menu item.",
            reply_markup=get_back_button()
        )


@require_auth
async def handle_menu_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route text messages based on menu_state"""
    menu_state = context.user_data.get('menu_state')

    logger.info(f"handle_menu_message called, current state: {menu_state}")

    # If not in a menu conversation, ignore
    if not menu_state:
        return

    # Route to appropriate handler based on state
    if menu_state == 'MENU_NAME':
        await receive_menu_name(update, context)
    elif menu_state == 'MENU_SIZE':
        await receive_menu_size(update, context)
    elif menu_state == 'MENU_PRICE':
        await receive_menu_price(update, context)
