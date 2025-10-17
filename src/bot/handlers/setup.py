"""
Menu setup handlers
"""
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from src.bot.middleware import require_auth
from src.database.models import Database
from src.bot.keyboards import get_menu_management_keyboard, get_back_button
from src.utils.formatters import format_menu_list

# Conversation states
MENU_NAME, MENU_SIZE, MENU_PRICE = range(3)

db = Database()


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
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text(
            "➕ *Add New Menu Item*\n\n"
            "Please enter the item name (e.g., 'Hojicha', 'Matcha'):\n\n"
            "Send /cancel to abort.",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "➕ *Add New Menu Item*\n\n"
            "Please enter the item name (e.g., 'Hojicha', 'Matcha'):\n\n"
            "Send /cancel to abort.",
            parse_mode="Markdown"
        )

    return MENU_NAME


@require_auth
async def receive_menu_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive the menu item name"""
    name = update.message.text.strip()

    if not name:
        await update.message.reply_text("❌ Item name cannot be empty. Please try again:")
        return MENU_NAME

    # Store in context
    context.user_data['new_menu_item'] = {'name': name}

    await update.message.reply_text(
        f"✅ Item name: *{name}*\n\n"
        "Now enter the size (e.g., 'Reg', 'Large', 'Small'):",
        parse_mode="Markdown"
    )

    return MENU_SIZE


@require_auth
async def receive_menu_size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive the menu item size"""
    size = update.message.text.strip()

    if not size:
        await update.message.reply_text("❌ Size cannot be empty. Please try again:")
        return MENU_SIZE

    # Store in context
    context.user_data['new_menu_item']['size'] = size

    await update.message.reply_text(
        f"✅ Size: *{size}*\n\n"
        "Now enter the price (numbers only, e.g., '4.50'):",
        parse_mode="Markdown"
    )

    return MENU_PRICE


@require_auth
async def receive_menu_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive the menu item price and save"""
    price_text = update.message.text.strip()

    try:
        price = float(price_text)
        if price <= 0:
            raise ValueError("Price must be positive")
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid price. Please enter a valid number (e.g., '4.50'):"
        )
        return MENU_PRICE

    # Get item data from context
    item_data = context.user_data.get('new_menu_item', {})
    name = item_data.get('name')
    size = item_data.get('size')

    # Save to database
    result = db.add_menu_item(name, size, price)

    if result:
        await update.message.reply_text(
            f"✅ *Menu Item Added!*\n\n"
            f"*Name:* {name}\n"
            f"*Size:* {size}\n"
            f"*Price:* ${price:.2f}\n\n"
            "Use /menu to manage your menu items.",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "❌ Failed to add menu item. Please try again later."
        )

    # Clear context
    context.user_data.pop('new_menu_item', None)

    return ConversationHandler.END


@require_auth
async def cancel_menu_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel menu item setup"""
    context.user_data.pop('new_menu_item', None)

    await update.message.reply_text(
        "❌ Menu item setup cancelled.",
        reply_markup=get_back_button()
    )

    return ConversationHandler.END


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
