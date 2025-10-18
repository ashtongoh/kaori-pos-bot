"""
Inventory input handlers - Manual state management
"""
from telegram import Update
from telegram.ext import ContextTypes
from src.bot.middleware import require_auth
from src.database.models import Database
from src.utils.formatters import format_inventory_list, format_currency, format_user_display_name
from src.utils.timezone import format_full_datetime
from src.bot.keyboards import (
    get_inventory_start_keyboard,
    get_add_another_inventory_keyboard,
    get_inventory_skip_price_keyboard,
    get_control_panel_keyboard,
    get_sales_dashboard_keyboard
)

db = Database()


@require_auth
async def start_session_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start a new sale session - begins with inventory input"""
    query = update.callback_query
    await query.answer()

    # Check if there's already an active session
    active_session = db.get_active_session()
    if active_session:
        await query.edit_message_text(
            "⚠️ There is already an active session!\n\n"
            "Please end the current session first."
        )
        return

    # Initialize inventory list in context
    context.user_data['inventory'] = []
    context.user_data['inventory_state'] = None

    await query.edit_message_text(
        "📦 *Starting New Session*\n\n"
        "Would you like to log your starting inventory?\n\n"
        "You can add inventory items now, skip, or cancel:",
        reply_markup=get_inventory_start_keyboard(),
        parse_mode="Markdown"
    )


@require_auth
async def start_adding_inventory_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User chose to start adding inventory"""
    query = update.callback_query
    await query.answer()

    # Set state to expect item name
    context.user_data['inventory_state'] = 'AWAITING_ITEM_NAME'

    inventory = context.user_data.get('inventory', [])

    if inventory:
        # Show current inventory if any items already added
        inv_text = format_inventory_list(inventory)
        await query.edit_message_text(
            f"📦 *Current Inventory:*\n\n{inv_text}\n\n"
            "Enter the name of the next inventory item:",
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text(
            "📦 *Adding Inventory*\n\n"
            "Enter the name of the inventory item:",
            parse_mode="Markdown"
        )


@require_auth
async def skip_inventory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Skip inventory input (works for both command and callback)"""
    # Handle callback query
    if update.callback_query:
        await update.callback_query.answer("Skipping inventory...")

    context.user_data['inventory'] = []
    context.user_data['inventory_state'] = None
    return await finish_inventory_input(update, context)


@require_auth
async def cancel_session_start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel session start and return to control panel"""
    query = update.callback_query
    await query.answer()

    # Clear inventory data
    context.user_data.pop('inventory', None)
    context.user_data.pop('inventory_state', None)
    context.user_data.pop('current_inv_item', None)

    await query.edit_message_text(
        "❌ *Session Creation Cancelled*\n\n"
        "Returning to control panel...",
        reply_markup=get_control_panel_keyboard(),
        parse_mode="Markdown"
    )


@require_auth
async def add_another_inventory_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'add another inventory item?' yes/no buttons"""
    query = update.callback_query
    response = query.data.split(':')[1]  # 'yes' or 'no'
    await query.answer()

    if response == 'yes':
        # Set state to expect item name
        context.user_data['inventory_state'] = 'AWAITING_ITEM_NAME'

        inventory = context.user_data.get('inventory', [])
        inv_text = format_inventory_list(inventory)

        await query.edit_message_text(
            f"📦 *Current Inventory:*\n\n{inv_text}\n\n"
            "Enter the name of the next inventory item:",
            parse_mode="Markdown"
        )
    else:
        # User said no, finish inventory input
        await finish_inventory_input(update, context)


@require_auth
async def skip_inventory_price_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Skip cost price input"""
    query = update.callback_query
    await query.answer()

    # Don't set cost_price, just add the item to inventory
    current_item = context.user_data.get('current_inv_item', {})

    # Add to inventory list
    inventory = context.user_data.get('inventory', [])
    inventory.append(current_item)
    context.user_data['inventory'] = inventory

    # Clear current item and state
    context.user_data.pop('current_inv_item', None)
    context.user_data['inventory_state'] = None

    # Show current inventory and ask if they want to add more
    inv_text = format_inventory_list(inventory)

    await query.edit_message_text(
        f"✅ *Item Added!*\n\n"
        f"{inv_text}\n\n"
        "Add another inventory item?",
        reply_markup=get_add_another_inventory_keyboard(),
        parse_mode="Markdown"
    )


@require_auth
async def handle_inventory_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages during inventory input flow"""
    state = context.user_data.get('inventory_state')

    if not state:
        return  # Not in inventory flow, ignore

    if state == 'AWAITING_ITEM_NAME':
        await receive_inventory_item_name(update, context)
    elif state == 'AWAITING_QUANTITY':
        await receive_inventory_quantity(update, context)
    elif state == 'AWAITING_COST_PRICE':
        await receive_inventory_price(update, context)


async def receive_inventory_item_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive inventory item name"""
    item_name = update.message.text.strip()

    if not item_name:
        await update.message.reply_text("❌ Item name cannot be empty. Please try again:")
        return

    # Store temporarily
    context.user_data['current_inv_item'] = {'item_name': item_name}
    context.user_data['inventory_state'] = 'AWAITING_QUANTITY'

    await update.message.reply_text(
        f"✅ Item: *{item_name}*\n\n"
        "Enter the quantity (number only):",
        parse_mode="Markdown"
    )


async def receive_inventory_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive inventory quantity"""
    quantity_text = update.message.text.strip()

    try:
        quantity = int(quantity_text)
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid quantity. Please enter a valid number:"
        )
        return

    # Store quantity
    context.user_data['current_inv_item']['quantity'] = quantity
    context.user_data['inventory_state'] = 'AWAITING_COST_PRICE'

    await update.message.reply_text(
        f"✅ Quantity: *{quantity}*\n\n"
        "Enter the cost price, or click Skip if not tracking cost:",
        reply_markup=get_inventory_skip_price_keyboard(),
        parse_mode="Markdown"
    )


async def receive_inventory_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive inventory cost price"""
    price_text = update.message.text.strip()

    try:
        cost_price = float(price_text)
        if cost_price < 0:
            raise ValueError("Price cannot be negative")
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid price. Please enter a valid number (or click Skip):"
        )
        return

    # Store cost price
    context.user_data['current_inv_item']['cost_price'] = cost_price

    # Add to inventory list
    inventory = context.user_data.get('inventory', [])
    inventory.append(context.user_data['current_inv_item'])
    context.user_data['inventory'] = inventory

    # Clear current item and state
    context.user_data.pop('current_inv_item', None)
    context.user_data['inventory_state'] = None

    # Show current inventory and ask if they want to add more
    inv_text = format_inventory_list(inventory)

    await update.message.reply_text(
        f"✅ *Item Added!*\n\n"
        f"{inv_text}\n\n"
        "Add another inventory item?",
        reply_markup=get_add_another_inventory_keyboard(),
        parse_mode="Markdown"
    )


async def finish_inventory_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Finish inventory input and create session"""
    inventory = context.user_data.get('inventory', [])

    # Create session
    telegram_id = update.effective_user.id
    session = db.create_session(telegram_id)

    if not session:
        # Handle both callback query and message
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "❌ Failed to create session. Please try again later."
            )
        else:
            await update.message.reply_text(
                "❌ Failed to create session. Please try again later."
            )
        return

    # Save inventory logs
    for inv_item in inventory:
        db.add_inventory_log(
            session['id'],
            inv_item['item_name'],
            inv_item['quantity'],
            inv_item.get('cost_price')
        )

    # Clear context
    context.user_data.pop('inventory', None)
    context.user_data.pop('inventory_state', None)
    context.user_data.pop('current_inv_item', None)

    # Show sales dashboard
    from src.bot.handlers.sales import show_sales_dashboard

    # Handle both callback query and message
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "✅ *Session Started!*\n\n"
            "Your sale session is now active.",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "✅ *Session Started!*\n\n"
            "Your sale session is now active.",
            parse_mode="Markdown"
        )

    # Store session ID
    context.user_data['active_session_id'] = session['id']

    # Show dashboard directly after session creation
    # Get session details for dashboard
    session_refreshed = db.get_active_session()
    if session_refreshed:
        order_count = db.get_order_count_by_session(session_refreshed['id'])
        total_sales = session_refreshed.get('total_sales', 0)
        started_at = format_full_datetime(session_refreshed.get('started_at'))
        started_by_id = session_refreshed.get('started_by')

        # Get user info for display name
        user_info = db.get_user_by_telegram_id(started_by_id) if started_by_id else None
        started_by_name = format_user_display_name(
            started_by_id,
            user_info.get('full_name') if user_info else None
        )

        dashboard_text = (
            f"💰 *Sales Dashboard*\n\n"
            f"🟢 Session started: {started_at}\n"
            f"👤 Started by: {started_by_name}\n\n"
            f"💵 *Total Sales:* {format_currency(total_sales)}\n"
            f"📝 *Orders:* {order_count}\n\n"
            f"Choose an option:"
        )

        # Send new message with dashboard keyboard
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=dashboard_text,
            reply_markup=get_sales_dashboard_keyboard(total_sales),
            parse_mode="Markdown"
        )
