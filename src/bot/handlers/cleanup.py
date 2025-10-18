"""
Cleanup handlers for deleting past sales and inventory
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from src.bot.middleware import require_auth_callback
from src.database.models import Database
from src.bot.keyboards import (
    get_cleanup_menu_keyboard,
    get_past_sales_cleanup_keyboard,
    get_past_inventory_cleanup_keyboard,
    get_confirm_delete_session_keyboard,
    get_confirm_purge_all_keyboard,
    get_control_panel_keyboard
)
from src.utils.timezone import format_full_datetime

db = Database()
logger = logging.getLogger(__name__)


@require_auth_callback
async def cleanup_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show cleanup menu"""
    query = update.callback_query

    await query.edit_message_text(
        "🗑 *Cleanup Menu*\n\n"
        "Select what you want to clean up:\n\n"
        "⚠️ *Warning:* Deleted data cannot be recovered!",
        reply_markup=get_cleanup_menu_keyboard(),
        parse_mode="Markdown"
    )


@require_auth_callback
async def cleanup_sales_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of past sales sessions for cleanup"""
    query = update.callback_query

    # Extract page number from callback data if present
    page = 0
    if ':' in query.data:
        page = int(query.data.split(':')[1])

    # Get past sessions (not active)
    limit = 10
    offset = page * limit
    sessions = db.get_past_sessions(limit=limit, offset=offset)

    # Filter out active sessions
    sessions = [s for s in sessions if s.get('status') == 'ended']

    if not sessions:
        await query.edit_message_text(
            "🗑 *Cleanup Past Sales*\n\n"
            "No past sales sessions found.\n\n"
            "All sessions have been cleaned up or no sessions exist yet.",
            reply_markup=get_cleanup_menu_keyboard(),
            parse_mode="Markdown"
        )
        return

    # Build session list text
    text = f"🗑 *Cleanup Past Sales*\n\n"
    text += f"Select a session to delete (showing {len(sessions)} sessions):\n\n"

    # Calculate total pages
    total_count = len(sessions)
    total_pages = (total_count + limit - 1) // limit

    await query.edit_message_text(
        text,
        reply_markup=get_past_sales_cleanup_keyboard(sessions, page, total_pages),
        parse_mode="Markdown"
    )


@require_auth_callback
async def cleanup_inventory_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of sessions with inventory for cleanup"""
    query = update.callback_query

    # Extract page number from callback data if present
    page = 0
    if ':' in query.data:
        page = int(query.data.split(':')[1])

    # Get sessions with inventory
    limit = 10
    offset = page * limit
    sessions = db.get_sessions_with_inventory(limit=limit, offset=offset)

    if not sessions:
        await query.edit_message_text(
            "🗑 *Cleanup Past Inventory*\n\n"
            "No sessions with inventory logs found.\n\n"
            "All inventory has been cleaned up or no inventory exists yet.",
            reply_markup=get_cleanup_menu_keyboard(),
            parse_mode="Markdown"
        )
        return

    # Build session list text
    text = f"🗑 *Cleanup Past Inventory*\n\n"
    text += f"Select a session to delete inventory (showing {len(sessions)} sessions):\n\n"

    # Calculate total pages
    total_count = len(sessions)
    total_pages = (total_count + limit - 1) // limit

    await query.edit_message_text(
        text,
        reply_markup=get_past_inventory_cleanup_keyboard(sessions, page, total_pages),
        parse_mode="Markdown"
    )


@require_auth_callback
async def confirm_delete_session_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show confirmation dialog for deleting a session"""
    query = update.callback_query

    # Extract session ID from callback data
    session_id = query.data.split(':')[1]

    # Get session details
    session = db.get_session_by_id(session_id)
    if not session:
        await query.edit_message_text(
            "❌ Session not found.",
            reply_markup=get_cleanup_menu_keyboard()
        )
        return

    # Get order count
    order_count = db.get_order_count_by_session(session_id)

    # Get inventory count
    inventory = db.get_inventory_by_session(session_id)
    inventory_count = len(inventory) if inventory else 0

    # Format session info
    started_at = format_full_datetime(session.get('started_at'))
    ended_at = format_full_datetime(session.get('ended_at')) if session.get('ended_at') else "N/A"

    text = f"⚠️ *Confirm Delete Session*\n\n"
    text += f"Started: {started_at}\n"
    text += f"Ended: {ended_at}\n"
    text += f"Orders: {order_count}\n"
    text += f"Inventory Logs: {inventory_count}\n\n"
    text += "🚨 *This will permanently delete:*\n"
    text += f"• The session record\n"
    text += f"• All {order_count} orders in this session\n"
    text += f"• All {inventory_count} inventory logs\n\n"
    text += "❌ *This action cannot be undone!*\n\n"
    text += "Are you sure you want to delete this session?"

    await query.edit_message_text(
        text,
        reply_markup=get_confirm_delete_session_keyboard(session_id),
        parse_mode="Markdown"
    )


@require_auth_callback
async def delete_session_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete a session and all related data"""
    query = update.callback_query

    # Extract session ID from callback data
    session_id = query.data.split(':')[1]

    # Get session details before deletion
    session = db.get_session_by_id(session_id)
    if not session:
        await query.edit_message_text(
            "❌ Session not found.",
            reply_markup=get_cleanup_menu_keyboard()
        )
        return

    # Delete session (cascade will delete orders and inventory)
    success = db.delete_session(session_id)

    if success:
        started_at = format_full_datetime(session.get('started_at'))
        await query.edit_message_text(
            f"✅ *Session Deleted*\n\n"
            f"Session from {started_at} has been permanently deleted.\n\n"
            "All orders and inventory logs have been removed.\n\n"
            "Returning to cleanup menu...",
            parse_mode="Markdown"
        )

        # Wait a moment then show cleanup menu
        import asyncio
        await asyncio.sleep(1.5)
        await query.edit_message_text(
            "🗑 *Cleanup Menu*\n\n"
            "Select what you want to clean up:\n\n"
            "⚠️ *Warning:* Deleted data cannot be recovered!",
            reply_markup=get_cleanup_menu_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text(
            "❌ Failed to delete session. Please try again.",
            reply_markup=get_cleanup_menu_keyboard()
        )


@require_auth_callback
async def cancel_cleanup_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel cleanup and return to cleanup menu"""
    query = update.callback_query

    await query.edit_message_text(
        "🗑 *Cleanup Menu*\n\n"
        "Select what you want to clean up:\n\n"
        "⚠️ *Warning:* Deleted data cannot be recovered!",
        reply_markup=get_cleanup_menu_keyboard(),
        parse_mode="Markdown"
    )


@require_auth_callback
async def confirm_purge_all_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show confirmation dialog for purging all past data"""
    query = update.callback_query

    # Get count of past sessions
    all_sessions = db.get_past_sessions(limit=10000, offset=0)
    ended_sessions = [s for s in all_sessions if s.get('status') == 'ended']

    if not ended_sessions:
        await query.edit_message_text(
            "🗑 *Purge All Past Data*\n\n"
            "No past sessions found to purge.\n\n"
            "All data has already been cleaned up!",
            reply_markup=get_cleanup_menu_keyboard(),
            parse_mode="Markdown"
        )
        return

    # Count total orders and inventory
    total_orders = 0
    total_inventory = 0

    for session in ended_sessions:
        total_orders += db.get_order_count_by_session(session['id'])
        inventory = db.get_inventory_by_session(session['id'])
        total_inventory += len(inventory) if inventory else 0

    text = f"⚠️ *PURGE ALL PAST DATA*\n\n"
    text += f"🚨 *WARNING:* This will permanently delete:\n\n"
    text += f"• *{len(ended_sessions)} past sale sessions*\n"
    text += f"• *{total_orders} orders*\n"
    text += f"• *{total_inventory} inventory logs*\n\n"
    text += "❌ *THIS ACTION CANNOT BE UNDONE!*\n\n"
    text += "Only active sessions will be preserved.\n\n"
    text += "Are you ABSOLUTELY SURE you want to purge all past data?"

    await query.edit_message_text(
        text,
        reply_markup=get_confirm_purge_all_keyboard(),
        parse_mode="Markdown"
    )


@require_auth_callback
async def purge_all_confirmed_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute purge all past data"""
    query = update.callback_query

    # Show processing message
    await query.edit_message_text(
        "🔄 *Purging all past data...*\n\n"
        "Please wait, this may take a moment...",
        parse_mode="Markdown"
    )

    # Execute purge
    result = db.purge_all_past_sessions()

    if result['sessions'] > 0:
        await query.edit_message_text(
            f"✅ *Purge Complete*\n\n"
            f"Successfully deleted:\n\n"
            f"• {result['sessions']} sessions\n"
            f"• {result['orders']} orders\n"
            f"• {result['inventory']} inventory logs\n\n"
            "All past data has been permanently removed.",
            parse_mode="Markdown"
        )

        # Wait a moment then show cleanup menu
        import asyncio
        await asyncio.sleep(2)
        await query.edit_message_text(
            "🗑 *Cleanup Menu*\n\n"
            "Select what you want to clean up:\n\n"
            "⚠️ *Warning:* Deleted data cannot be recovered!",
            reply_markup=get_cleanup_menu_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text(
            "❌ No data was purged.\n\n"
            "Either no past sessions exist or an error occurred.",
            reply_markup=get_cleanup_menu_keyboard(),
            parse_mode="Markdown"
        )
