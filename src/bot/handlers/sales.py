"""
Active sale session handlers
"""
from telegram import Update
from telegram.ext import ContextTypes
from src.bot.middleware import require_auth, require_auth_callback
from src.database.models import Database
from src.bot.keyboards import (
    get_sales_dashboard_keyboard,
    get_menu_items_keyboard,
    get_payment_method_keyboard,
    get_confirm_end_session_keyboard,
    get_control_panel_keyboard
)
from src.utils.formatters import format_currency, format_cart, format_session_summary
from src.utils.timezone import get_singapore_time, format_full_datetime

db = Database()


@require_auth
async def show_sales_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the active sales dashboard"""
    # Get active session
    session = db.get_active_session()

    if not session:
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "⚠️ No active session found.\n\n"
                "Please start a new session from the control panel.",
                reply_markup=get_control_panel_keyboard()
            )
        else:
            await update.message.reply_text(
                "⚠️ No active session found.\n\n"
                "Please start a new session from the control panel.",
                reply_markup=get_control_panel_keyboard()
            )
        return

    # Get order count for session
    order_count = db.get_order_count_by_session(session['id'])
    total_sales = session.get('total_sales', 0)

    text = (
        f"🟢 *Active Session*\n\n"
        f"💰 *Total Sales:* {format_currency(total_sales)}\n"
        f"📝 *Orders:* {order_count}\n\n"
        f"Choose an option:"
    )

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=get_sales_dashboard_keyboard(total_sales),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=get_sales_dashboard_keyboard(total_sales),
            parse_mode="Markdown"
        )


@require_auth_callback
async def new_order_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start a new order"""
    query = update.callback_query
    await query.answer()

    # Get active session
    session = db.get_active_session()
    if not session:
        await query.edit_message_text(
            "⚠️ No active session found.",
            reply_markup=get_control_panel_keyboard()
        )
        return

    # Initialize cart in context
    context.user_data['cart'] = {}
    context.user_data['session_id'] = session['id']

    # Get menu items
    menu_items = db.get_menu_items()

    if not menu_items:
        await query.edit_message_text(
            "❌ No menu items found.\n\n"
            "Please add menu items first.",
            reply_markup=get_sales_dashboard_keyboard(session.get('total_sales', 0))
        )
        return

    # Show menu with cart
    cart_display = format_cart(context.user_data['cart'])
    await query.edit_message_text(
        f"{cart_display}\n\n📋 *Select items to add to cart:*",
        reply_markup=get_menu_items_keyboard(menu_items, context.user_data['cart']),
        parse_mode="Markdown"
    )


@require_auth_callback
async def add_item_to_cart_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add an item to the cart"""
    query = update.callback_query
    await query.answer("Item added!")

    # Extract item ID from callback data
    item_id = query.data.split(':')[1]

    # Get menu items
    menu_items = db.get_menu_items()
    menu_dict = {item['id']: item for item in menu_items}

    if item_id not in menu_dict:
        await query.answer("❌ Item not found", show_alert=True)
        return

    # Get or initialize cart
    cart = context.user_data.get('cart', {})

    # Add or increment item
    if item_id in cart:
        cart[item_id]['quantity'] += 1
    else:
        item = menu_dict[item_id]
        cart[item_id] = {
            'name': item['name'],
            'size': item['size'],
            'price': item['price'],
            'quantity': 1
        }

    context.user_data['cart'] = cart

    # Update display
    cart_display = format_cart(cart)
    await query.edit_message_text(
        f"{cart_display}\n\n📋 *Select items to add to cart:*",
        reply_markup=get_menu_items_keyboard(menu_items, cart),
        parse_mode="Markdown"
    )


@require_auth_callback
async def clear_cart_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear the cart"""
    query = update.callback_query
    await query.answer("Cart cleared!")

    # Clear cart
    context.user_data['cart'] = {}

    # Get menu items
    menu_items = db.get_menu_items()

    # Update display
    cart_display = format_cart(context.user_data['cart'])
    await query.edit_message_text(
        f"{cart_display}\n\n📋 *Select items to add to cart:*",
        reply_markup=get_menu_items_keyboard(menu_items, context.user_data['cart']),
        parse_mode="Markdown"
    )


@require_auth_callback
async def confirm_cart_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm cart and proceed to payment"""
    query = update.callback_query
    await query.answer()

    cart = context.user_data.get('cart', {})

    if not cart:
        await query.answer("❌ Cart is empty!", show_alert=True)
        return

    # Show payment method selection
    cart_display = format_cart(cart)
    await query.edit_message_text(
        f"{cart_display}\n\n💳 *Select Payment Method:*",
        reply_markup=get_payment_method_keyboard(),
        parse_mode="Markdown"
    )


@require_auth_callback
async def payment_method_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment method selection and create order"""
    query = update.callback_query
    await query.answer()

    # Extract payment method
    payment_method = query.data.split(':')[1]

    cart = context.user_data.get('cart', {})
    session_id = context.user_data.get('session_id')

    if not cart or not session_id:
        await query.edit_message_text(
            "❌ Something went wrong. Please try again.",
            reply_markup=get_sales_dashboard_keyboard(0)
        )
        return

    # Convert cart to items list
    items = [
        {
            'menu_item_id': item_id,
            'name': item_data['name'],
            'size': item_data['size'],
            'price': float(item_data['price']),
            'quantity': item_data['quantity']
        }
        for item_id, item_data in cart.items()
    ]

    # Create order
    telegram_id = update.effective_user.id
    order = db.create_order(session_id, items, payment_method, telegram_id)

    if order:
        # Clear cart
        context.user_data.pop('cart', None)

        # Show success message
        await query.edit_message_text(
            f"✅ *Order Created!*\n\n"
            f"Order #{order['order_number']}\n"
            f"Total: {format_currency(order['total_amount'])}\n"
            f"Payment: {payment_method.title()}\n\n"
            f"Returning to dashboard...",
            parse_mode="Markdown"
        )

        # Wait a moment then show dashboard
        import asyncio
        await asyncio.sleep(2)
        await show_sales_dashboard(update, context)
    else:
        await query.edit_message_text(
            "❌ Failed to create order. Please try again.",
            reply_markup=get_sales_dashboard_keyboard(0)
        )


@require_auth_callback
async def cancel_order_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel order creation"""
    query = update.callback_query
    await query.answer("Order cancelled")

    # Clear cart
    context.user_data.pop('cart', None)

    # Return to dashboard
    await show_sales_dashboard(update, context)


@require_auth_callback
async def cancel_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel payment and go back to cart"""
    query = update.callback_query
    await query.answer()

    # Get menu items and cart
    menu_items = db.get_menu_items()
    cart = context.user_data.get('cart', {})

    # Show cart again
    cart_display = format_cart(cart)
    await query.edit_message_text(
        f"{cart_display}\n\n📋 *Select items to add to cart:*",
        reply_markup=get_menu_items_keyboard(menu_items, cart),
        parse_mode="Markdown"
    )


@require_auth_callback
async def end_session_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show confirmation for ending session"""
    query = update.callback_query
    await query.answer()

    # Get active session
    session = db.get_active_session()
    if not session:
        await query.edit_message_text(
            "⚠️ No active session found.",
            reply_markup=get_control_panel_keyboard()
        )
        return

    current_time = format_full_datetime(get_singapore_time())

    await query.edit_message_text(
        f"⚠️ *Confirm End Session*\n\n"
        f"Are you sure you want to end this session?\n\n"
        f"Current time: {current_time}\n"
        f"Total sales: {format_currency(session.get('total_sales', 0))}",
        reply_markup=get_confirm_end_session_keyboard(),
        parse_mode="Markdown"
    )


@require_auth_callback
async def confirm_end_session_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and end the session"""
    query = update.callback_query
    await query.answer()

    # Get active session
    session = db.get_active_session()
    if not session:
        await query.edit_message_text(
            "⚠️ No active session found.",
            reply_markup=get_control_panel_keyboard()
        )
        return

    session_id = session['id']

    # Get session statistics
    order_count = db.get_order_count_by_session(session_id)
    orders = db.get_orders_by_session(session_id, limit=1000)

    # Calculate items sold
    items_sold = {}
    for order in orders:
        for item in order['items']:
            item_key = f"{item['name']} ({item['size']})"
            items_sold[item_key] = items_sold.get(item_key, 0) + item['quantity']

    # End session
    success = db.end_session(session_id)

    if success:
        summary = format_session_summary(session, order_count, items_sold)
        await query.edit_message_text(
            f"✅ *Session Ended*\n\n{summary}",
            reply_markup=get_control_panel_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text(
            "❌ Failed to end session. Please try again.",
            reply_markup=get_sales_dashboard_keyboard(session.get('total_sales', 0))
        )


@require_auth_callback
async def back_to_dashboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to sales dashboard"""
    query = update.callback_query
    await query.answer()

    await show_sales_dashboard(update, context)
