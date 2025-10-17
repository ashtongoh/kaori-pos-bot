"""
Inventory input handlers
"""
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from src.bot.middleware import require_auth
from src.database.models import Database
from src.utils.formatters import format_inventory_list

# Conversation states
INV_ITEM_NAME, INV_QUANTITY, INV_PRICE, INV_MORE = range(4)

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
        return ConversationHandler.END

    # Initialize inventory list in context
    context.user_data['inventory'] = []

    await query.edit_message_text(
        "📦 *Starting New Session*\n\n"
        "Let's log your starting inventory.\n\n"
        "Enter the item name (or send /skip to skip inventory):",
        parse_mode="Markdown"
    )

    return INV_ITEM_NAME


@require_auth
async def receive_inventory_item_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive inventory item name"""
    item_name = update.message.text.strip()

    if not item_name:
        await update.message.reply_text("❌ Item name cannot be empty. Please try again:")
        return INV_ITEM_NAME

    # Store temporarily
    context.user_data['current_inv_item'] = {'item_name': item_name}

    await update.message.reply_text(
        f"✅ Item: *{item_name}*\n\n"
        "Enter the quantity (number only):",
        parse_mode="Markdown"
    )

    return INV_QUANTITY


@require_auth
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
        return INV_QUANTITY

    # Store quantity
    context.user_data['current_inv_item']['quantity'] = quantity

    await update.message.reply_text(
        f"✅ Quantity: *{quantity}*\n\n"
        "Enter the cost price (or send /skip if not tracking cost):",
        parse_mode="Markdown"
    )

    return INV_PRICE


@require_auth
async def receive_inventory_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive inventory cost price"""
    price_text = update.message.text.strip()

    cost_price = None
    if price_text.lower() != '/skip':
        try:
            cost_price = float(price_text)
            if cost_price < 0:
                raise ValueError("Price cannot be negative")
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid price. Please enter a valid number (or /skip):"
            )
            return INV_PRICE

    # Store cost price
    if cost_price is not None:
        context.user_data['current_inv_item']['cost_price'] = cost_price

    # Add to inventory list
    inventory = context.user_data.get('inventory', [])
    inventory.append(context.user_data['current_inv_item'])
    context.user_data['inventory'] = inventory

    # Clear current item
    context.user_data.pop('current_inv_item', None)

    # Show current inventory
    inv_text = format_inventory_list(inventory)

    await update.message.reply_text(
        f"{inv_text}\n\n"
        "Add another item? (yes/no):"
    )

    return INV_MORE


@require_auth
async def ask_more_inventory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask if user wants to add more inventory"""
    response = update.message.text.strip().lower()

    if response in ['yes', 'y']:
        await update.message.reply_text("Enter the next item name:")
        return INV_ITEM_NAME
    elif response in ['no', 'n']:
        return await finish_inventory_input(update, context)
    else:
        await update.message.reply_text("Please respond with 'yes' or 'no':")
        return INV_MORE


@require_auth
async def skip_inventory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Skip inventory input"""
    context.user_data['inventory'] = []
    return await finish_inventory_input(update, context)


@require_auth
async def finish_inventory_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Finish inventory input and create session"""
    inventory = context.user_data.get('inventory', [])

    # Create session
    telegram_id = update.effective_user.id
    session = db.create_session(telegram_id)

    if not session:
        await update.message.reply_text(
            "❌ Failed to create session. Please try again later."
        )
        return ConversationHandler.END

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
    context.user_data.pop('current_inv_item', None)

    # Show sales dashboard
    from src.bot.handlers.sales import show_sales_dashboard
    await update.message.reply_text(
        "✅ *Session Started!*\n\n"
        "Your sale session is now active.",
        parse_mode="Markdown"
    )

    # Create a mock update object for showing dashboard
    context.user_data['active_session_id'] = session['id']
    return await show_sales_dashboard(update, context)


@require_auth
async def cancel_inventory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel inventory input"""
    context.user_data.pop('inventory', None)
    context.user_data.pop('current_inv_item', None)

    await update.message.reply_text(
        "❌ Session creation cancelled."
    )

    return ConversationHandler.END
