"""
Order management handlers
"""
from telegram import Update
from telegram.ext import ContextTypes
from src.bot.middleware import require_auth_callback
from src.database.models import Database
from src.bot.keyboards import (
    get_orders_list_keyboard,
    get_order_detail_keyboard,
    get_confirm_delete_keyboard,
    get_sales_dashboard_keyboard
)
from src.utils.formatters import format_order_summary
import math

db = Database()


@require_auth_callback
async def view_orders_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View all orders in current session"""
    query = update.callback_query
    await query.answer()

    # Get active session
    session = db.get_active_session()
    if not session:
        await query.edit_message_text(
            "⚠️ No active session found."
        )
        return

    # Get page number from callback data if present
    page = 0
    if ':' in query.data:
        page = int(query.data.split(':')[1])

    # Pagination settings
    per_page = 5
    offset = page * per_page

    # Get orders
    orders = db.get_orders_by_session(session['id'], limit=per_page, offset=offset)

    if not orders and page == 0:
        await query.edit_message_text(
            "📝 *Orders*\n\n"
            "No orders yet.",
            reply_markup=get_sales_dashboard_keyboard(session.get('total_sales', 0)),
            parse_mode="Markdown"
        )
        return

    # Calculate total pages
    total_orders = db.get_order_count_by_session(session['id'])
    total_pages = math.ceil(total_orders / per_page)

    # Show orders list
    await query.edit_message_text(
        f"📝 *Orders* (Page {page + 1}/{total_pages})\n\n"
        "Select an order to view details:",
        reply_markup=get_orders_list_keyboard(orders, page, total_pages),
        parse_mode="Markdown"
    )


@require_auth_callback
async def view_order_detail_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View order details"""
    query = update.callback_query
    await query.answer()

    # Extract order ID from callback data
    order_id = query.data.split(':')[1]

    # Get order
    order = db.get_order_by_id(order_id)

    if not order:
        await query.answer("❌ Order not found", show_alert=True)
        return

    # Format and show order details
    order_text = format_order_summary(order)

    await query.edit_message_text(
        order_text,
        reply_markup=get_order_detail_keyboard(order_id),
        parse_mode="Markdown"
    )


@require_auth_callback
async def delete_order_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show delete confirmation for an order"""
    query = update.callback_query
    await query.answer()

    # Extract order ID from callback data
    order_id = query.data.split(':')[1]

    # Get order
    order = db.get_order_by_id(order_id)

    if not order:
        await query.answer("❌ Order not found", show_alert=True)
        return

    await query.edit_message_text(
        f"⚠️ *Delete Order #{order['order_number']}?*\n\n"
        f"This will remove the order and update the session total.\n\n"
        f"Are you sure?",
        reply_markup=get_confirm_delete_keyboard(order_id),
        parse_mode="Markdown"
    )


@require_auth_callback
async def confirm_delete_order_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and delete an order"""
    query = update.callback_query
    await query.answer()

    # Extract order ID from callback data
    order_id = query.data.split(':')[1]

    # Get order before deletion
    order = db.get_order_by_id(order_id)

    if not order:
        await query.answer("❌ Order not found", show_alert=True)
        return

    order_number = order['order_number']

    # Delete order
    success = db.delete_order(order_id)

    if success:
        await query.edit_message_text(
            f"✅ Order #{order_number} deleted successfully!",
            parse_mode="Markdown"
        )

        # Wait a moment then return to orders view
        import asyncio
        await asyncio.sleep(2)

        # Reset callback data to view orders
        query.data = "view_orders"
        await view_orders_callback(update, context)
    else:
        await query.edit_message_text(
            "❌ Failed to delete order. Please try again."
        )
