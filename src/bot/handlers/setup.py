"""
Menu setup handlers
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from src.bot.middleware import require_auth
from src.database.models import Database
from src.bot.keyboards import (
    get_menu_management_keyboard,
    get_back_button,
    get_cancel_button,
    get_add_another_menu_item_keyboard,
    get_yes_no_keyboard,
    get_edit_menu_item_keyboard,
    get_confirm_delete_menu_item_keyboard,
    get_back_to_menu_keyboard
)
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
    context.user_data['new_menu_item']['sizes'] = []  # Initialize sizes list
    context.user_data['menu_state'] = 'MENU_HAS_SIZES'
    logger.info(f"Stored name in context: {name}, moving to MENU_HAS_SIZES state")

    await update.message.reply_text(
        f"✅ Item name: *{name}*\n\n"
        "Does this item have multiple sizes?\n"
        "(e.g., Regular, Large, etc.)",
        reply_markup=get_yes_no_keyboard("has_multiple_sizes:yes", "has_multiple_sizes:no"),
        parse_mode="Markdown"
    )


@require_auth
async def handle_has_sizes_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button click for has_multiple_sizes question"""
    query = update.callback_query
    await query.answer()

    # Extract response from callback data
    response = query.data.split(':')[1]  # "yes" or "no"
    item_name = context.user_data['new_menu_item']['name']

    if response == 'yes':
        # Item has multiple sizes
        context.user_data['new_menu_item']['has_multiple_sizes'] = True
        context.user_data['menu_state'] = 'MENU_SIZE'

        await query.edit_message_text(
            f"✅ Got it! *{item_name}* has multiple sizes.\n\n"
            "Let's add the first size.\n\n"
            "Enter the size name (e.g., 'Regular', 'Large', 'Small'):",
            reply_markup=get_cancel_button(),
            parse_mode="Markdown"
        )
    else:
        # Single size item - go straight to price
        context.user_data['new_menu_item']['has_multiple_sizes'] = False
        context.user_data['new_menu_item']['size'] = 'Standard'  # Default size name
        context.user_data['menu_state'] = 'MENU_PRICE'

        await query.edit_message_text(
            f"✅ Got it! *{item_name}* is a single-size item.\n\n"
            "Now enter the price (numbers only, e.g., '4.50'):",
            reply_markup=get_cancel_button(),
            parse_mode="Markdown"
        )


async def receive_menu_size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive the menu item size (for multi-size items)"""
    size = update.message.text.strip()

    if not size:
        await update.message.reply_text(
            "❌ Size cannot be empty. Please try again:",
            reply_markup=get_cancel_button()
        )
        return

    # Store current size temporarily
    context.user_data['new_menu_item']['current_size'] = size
    context.user_data['menu_state'] = 'MENU_SIZE_PRICE'

    await update.message.reply_text(
        f"✅ Size: *{size}*\n\n"
        "Now enter the price for this size (e.g., '4.50'):",
        reply_markup=get_cancel_button(),
        parse_mode="Markdown"
    )


async def receive_size_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive price for a specific size in multi-size items"""
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
    current_size = item_data.get('current_size')

    # Add this size to the sizes list
    item_data['sizes'].append({
        'size': current_size,
        'price': price
    })

    # Clear current_size
    item_data.pop('current_size', None)

    # Show current sizes and ask if they want to add more
    sizes_summary = "\n".join([f"  • {s['size']}: ${s['price']:.2f}" for s in item_data['sizes']])

    context.user_data['menu_state'] = 'MENU_ADD_MORE_SIZES'

    await update.message.reply_text(
        f"✅ Size added!\n\n"
        f"*Current sizes for {item_data['name']}:*\n{sizes_summary}\n\n"
        "Do you want to add another size?",
        reply_markup=get_yes_no_keyboard("add_more_sizes:yes", "add_more_sizes:no"),
        parse_mode="Markdown"
    )


@require_auth
async def handle_add_more_sizes_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button click for add more sizes question"""
    query = update.callback_query
    await query.answer()

    # Extract response from callback data
    response = query.data.split(':')[1]  # "yes" or "no"

    if response == 'yes':
        # Add another size
        context.user_data['menu_state'] = 'MENU_SIZE'
        item_name = context.user_data['new_menu_item']['name']

        await query.edit_message_text(
            f"Great! Let's add another size for *{item_name}*.\n\n"
            "Enter the size name (e.g., 'Large', 'Extra Large'):",
            reply_markup=get_cancel_button(),
            parse_mode="Markdown"
        )
    else:
        # Save all sizes to database
        await save_menu_items(update, context, query)


async def receive_menu_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive the menu item price and save (for single-size items)"""
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

    # Store price and save
    context.user_data['new_menu_item']['price'] = price
    await save_menu_items(update, context)


async def save_menu_items(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None):
    """Save menu item(s) to database"""
    item_data = context.user_data.get('new_menu_item', {})
    name = item_data.get('name')
    has_multiple_sizes = item_data.get('has_multiple_sizes', False)

    success_count = 0
    failed_count = 0

    # Determine how to send message (callback query or regular message)
    send_func = query.edit_message_text if query else update.message.reply_text

    if has_multiple_sizes:
        # Save each size as a separate menu item
        sizes = item_data.get('sizes', [])
        for size_data in sizes:
            result = db.add_menu_item(name, size_data['size'], size_data['price'])
            if result:
                success_count += 1
            else:
                failed_count += 1

        if success_count > 0:
            sizes_summary = "\n".join([f"  • {s['size']}: ${s['price']:.2f}" for s in sizes])
            await send_func(
                f"✅ *Menu Items Added Successfully!*\n\n"
                f"*{name}*\n{sizes_summary}\n\n"
                f"({success_count} size{'s' if success_count > 1 else ''} added)\n\n"
                "What would you like to do next?",
                reply_markup=get_add_another_menu_item_keyboard(),
                parse_mode="Markdown"
            )
        else:
            await send_func(
                "❌ Failed to add menu items. Please try again later.",
                reply_markup=get_back_button()
            )
    else:
        # Single size item
        size = item_data.get('size', 'Standard')
        price = item_data.get('price')
        result = db.add_menu_item(name, size, price)

        if result:
            await send_func(
                f"✅ *Menu Item Added Successfully!*\n\n"
                f"*Name:* {name}\n"
                f"*Price:* ${price:.2f}\n\n"
                "What would you like to do next?",
                reply_markup=get_add_another_menu_item_keyboard(),
                parse_mode="Markdown"
            )
        else:
            await send_func(
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
async def edit_menu_item_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show edit options for a menu item"""
    query = update.callback_query
    await query.answer()

    # Extract item ID from callback data
    item_id = query.data.split(':')[1]

    # Get item details from database
    menu_items = db.get_menu_items()
    item = next((i for i in menu_items if i['id'] == item_id), None)

    if not item:
        await query.edit_message_text(
            "❌ Menu item not found.",
            reply_markup=get_back_button()
        )
        return

    await query.edit_message_text(
        f"📝 *Edit Menu Item*\n\n"
        f"*Name:* {item['name']}\n"
        f"*Size:* {item['size']}\n"
        f"*Price:* ${item['price']:.2f}\n\n"
        "What would you like to do?",
        reply_markup=get_edit_menu_item_keyboard(item_id),
        parse_mode="Markdown"
    )


@require_auth
async def edit_name_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start editing name for a menu item"""
    query = update.callback_query
    await query.answer()

    # Extract item ID from callback data
    item_id = query.data.split(':')[1]

    # Store item ID in context
    context.user_data['editing_item_id'] = item_id
    context.user_data['menu_state'] = 'EDIT_NAME'

    # Get item details
    menu_items = db.get_menu_items()
    item = next((i for i in menu_items if i['id'] == item_id), None)

    if not item:
        await query.edit_message_text(
            "❌ Menu item not found.",
            reply_markup=get_back_button()
        )
        return

    await query.edit_message_text(
        f"📝 *Edit Name*\n\n"
        f"*Current Name:* {item['name']}\n"
        f"*Size:* {item['size']}\n"
        f"*Price:* ${item['price']:.2f}\n\n"
        "Enter the new name (e.g., 'Hojicha Latte'):",
        reply_markup=get_cancel_button(),
        parse_mode="Markdown"
    )


@require_auth
async def edit_size_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start editing size for a menu item"""
    query = update.callback_query
    await query.answer()

    # Extract item ID from callback data
    item_id = query.data.split(':')[1]

    # Store item ID in context
    context.user_data['editing_item_id'] = item_id
    context.user_data['menu_state'] = 'EDIT_SIZE'

    # Get item details
    menu_items = db.get_menu_items()
    item = next((i for i in menu_items if i['id'] == item_id), None)

    if not item:
        await query.edit_message_text(
            "❌ Menu item not found.",
            reply_markup=get_back_button()
        )
        return

    await query.edit_message_text(
        f"📏 *Edit Size*\n\n"
        f"*Name:* {item['name']}\n"
        f"*Current Size:* {item['size']}\n"
        f"*Price:* ${item['price']:.2f}\n\n"
        "Enter the new size (e.g., 'Large', 'Regular'):",
        reply_markup=get_cancel_button(),
        parse_mode="Markdown"
    )


@require_auth
async def edit_price_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start editing price for a menu item"""
    query = update.callback_query
    await query.answer()

    # Extract item ID from callback data
    item_id = query.data.split(':')[1]

    # Store item ID in context
    context.user_data['editing_item_id'] = item_id
    context.user_data['menu_state'] = 'EDIT_PRICE'

    # Get item details
    menu_items = db.get_menu_items()
    item = next((i for i in menu_items if i['id'] == item_id), None)

    if not item:
        await query.edit_message_text(
            "❌ Menu item not found.",
            reply_markup=get_back_button()
        )
        return

    await query.edit_message_text(
        f"💰 *Edit Price*\n\n"
        f"*Name:* {item['name']}\n"
        f"*Size:* {item['size']}\n"
        f"*Current Price:* ${item['price']:.2f}\n\n"
        "Enter the new price (e.g., '5.50'):",
        reply_markup=get_cancel_button(),
        parse_mode="Markdown"
    )


async def receive_edited_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive and save the new name"""
    new_name = update.message.text.strip()

    if not new_name:
        await update.message.reply_text(
            "❌ Name cannot be empty. Please try again:",
            reply_markup=get_cancel_button()
        )
        return

    # Get item ID from context
    item_id = context.user_data.get('editing_item_id')

    # Get old item details for comparison
    menu_items = db.get_menu_items()
    old_item = next((i for i in menu_items if i['id'] == item_id), None)

    # Update name in database
    success = db.update_menu_item_name(item_id, new_name)

    if success:
        await update.message.reply_text(
            f"✅ *Name Updated Successfully!*\n\n"
            f"*Old Name:* {old_item['name']}\n"
            f"*New Name:* {new_name}\n"
            f"*Size:* {old_item['size']}\n"
            f"*Price:* ${old_item['price']:.2f}",
            reply_markup=get_back_to_menu_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "❌ Failed to update name. Please try again later.",
            reply_markup=get_back_to_menu_keyboard()
        )

    # Clear context
    context.user_data.pop('editing_item_id', None)
    context.user_data.pop('menu_state', None)


async def receive_edited_size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive and save the new size"""
    new_size = update.message.text.strip()

    if not new_size:
        await update.message.reply_text(
            "❌ Size cannot be empty. Please try again:",
            reply_markup=get_cancel_button()
        )
        return

    # Get item ID from context
    item_id = context.user_data.get('editing_item_id')

    # Get old item details for comparison
    menu_items = db.get_menu_items()
    old_item = next((i for i in menu_items if i['id'] == item_id), None)

    # Update size in database
    success = db.update_menu_item_size(item_id, new_size)

    if success:
        await update.message.reply_text(
            f"✅ *Size Updated Successfully!*\n\n"
            f"*Name:* {old_item['name']}\n"
            f"*Old Size:* {old_item['size']}\n"
            f"*New Size:* {new_size}\n"
            f"*Price:* ${old_item['price']:.2f}",
            reply_markup=get_back_to_menu_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "❌ Failed to update size. Please try again later.",
            reply_markup=get_back_to_menu_keyboard()
        )

    # Clear context
    context.user_data.pop('editing_item_id', None)
    context.user_data.pop('menu_state', None)


async def receive_edited_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive and save the new price"""
    price_text = update.message.text.strip()

    try:
        price = float(price_text)
        if price <= 0:
            raise ValueError("Price must be positive")
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid price. Please enter a valid number (e.g., '5.50'):",
            reply_markup=get_cancel_button()
        )
        return

    # Get item ID from context
    item_id = context.user_data.get('editing_item_id')

    # Get old item details for comparison
    menu_items = db.get_menu_items()
    old_item = next((i for i in menu_items if i['id'] == item_id), None)

    # Update price in database
    success = db.update_menu_item_price(item_id, price)

    if success:
        await update.message.reply_text(
            f"✅ *Price Updated Successfully!*\n\n"
            f"*Name:* {old_item['name']}\n"
            f"*Size:* {old_item['size']}\n"
            f"*Old Price:* ${old_item['price']:.2f}\n"
            f"*New Price:* ${price:.2f}",
            reply_markup=get_back_to_menu_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "❌ Failed to update price. Please try again later.",
            reply_markup=get_back_to_menu_keyboard()
        )

    # Clear context
    context.user_data.pop('editing_item_id', None)
    context.user_data.pop('menu_state', None)


@require_auth
async def confirm_delete_menu_item_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show confirmation before deleting menu item"""
    query = update.callback_query
    await query.answer()

    # Extract item ID from callback data
    item_id = query.data.split(':')[1]

    # Get item details
    menu_items = db.get_menu_items()
    item = next((i for i in menu_items if i['id'] == item_id), None)

    if not item:
        await query.edit_message_text(
            "❌ Menu item not found.",
            reply_markup=get_back_button()
        )
        return

    await query.edit_message_text(
        f"🗑 *Confirm Deletion*\n\n"
        f"Are you sure you want to delete this item?\n\n"
        f"*Name:* {item['name']}\n"
        f"*Size:* {item['size']}\n"
        f"*Price:* ${item['price']:.2f}\n\n"
        "⚠️ This action cannot be undone.",
        reply_markup=get_confirm_delete_menu_item_keyboard(item_id),
        parse_mode="Markdown"
    )


@require_auth
async def delete_menu_item_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle menu item deletion after confirmation"""
    query = update.callback_query
    await query.answer()

    # Extract item ID from callback data
    item_id = query.data.split(':')[1]

    # Get item details before deletion
    menu_items = db.get_menu_items()
    item = next((i for i in menu_items if i['id'] == item_id), None)

    if not item:
        await query.edit_message_text(
            "❌ Menu item not found.",
            reply_markup=get_back_to_menu_keyboard()
        )
        return

    # Delete the item
    success = db.delete_menu_item(item_id)

    if success:
        await query.edit_message_text(
            f"✅ *Menu Item Deleted Successfully!*\n\n"
            f"The following item has been removed:\n\n"
            f"*Name:* {item['name']}\n"
            f"*Size:* {item['size']}\n"
            f"*Price:* ${item['price']:.2f}",
            reply_markup=get_back_to_menu_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text(
            f"❌ *Failed to Delete Menu Item*\n\n"
            f"Could not delete:\n"
            f"*{item['name']}* ({item['size']}) - ${item['price']:.2f}\n\n"
            "Please try again later.",
            reply_markup=get_back_to_menu_keyboard(),
            parse_mode="Markdown"
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
    elif menu_state == 'MENU_SIZE_PRICE':
        await receive_size_price(update, context)
    elif menu_state == 'MENU_PRICE':
        await receive_menu_price(update, context)
    elif menu_state == 'EDIT_NAME':
        await receive_edited_name(update, context)
    elif menu_state == 'EDIT_SIZE':
        await receive_edited_size(update, context)
    elif menu_state == 'EDIT_PRICE':
        await receive_edited_price(update, context)
