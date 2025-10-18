"""
Control panel handlers
"""
from telegram import Update
from telegram.ext import ContextTypes
from src.bot.middleware import require_auth
from src.database.models import Database
from src.bot.keyboards import get_control_panel_keyboard, get_pagination_keyboard
from src.utils.formatters import format_session_summary, format_inventory_list, format_user_display_name
from src.utils.timezone import format_full_datetime
import math

db = Database()


@require_auth
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user

    # Check if there's an active session
    active_session = db.get_active_session()

    if active_session:
        # Show control panel with active session info
        started_by_id = active_session.get('started_by')
        started_at = format_full_datetime(active_session.get('started_at'))

        # Get user info for display name
        user_info = db.get_user_by_telegram_id(started_by_id) if started_by_id else None
        started_by_name = format_user_display_name(
            started_by_id,
            user_info.get('full_name') if user_info else None
        )

        await update.message.reply_text(
            f"👋 Welcome back, {user.first_name}!\n\n"
            f"🟢 *Active Session*\n"
            f"Started: {started_at}\n"
            f"Started by: {started_by_name}\n\n"
            "Click 'Join Active Session' to continue working:",
            reply_markup=get_control_panel_keyboard(active_session),
            parse_mode="Markdown"
        )
    else:
        # Show control panel
        await update.message.reply_text(
            f"👋 Welcome to Kori POS, {user.first_name}!\n\n"
            "Use the buttons below to manage your business:",
            reply_markup=get_control_panel_keyboard()
        )


@require_auth
async def control_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show control panel"""
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    user_name = user.first_name

    # Check if there's an active session
    active_session = db.get_active_session()

    if active_session:
        # Show active session stats
        started_at = format_full_datetime(active_session.get('started_at'))
        total_sales = active_session.get('total_sales', 0)
        order_count = db.get_order_count_by_session(active_session['id'])

        await query.edit_message_text(
            f"🏠 *Control Panel*\n\n"
            f"👋 Welcome back, {user_name}!\n\n"
            f"🟢 *Active Session*\n"
            f"Started: {started_at}\n"
            f"💰 Sales: ${total_sales:.2f} | 📝 Orders: {order_count}\n\n"
            "Choose an option:",
            reply_markup=get_control_panel_keyboard(active_session),
            parse_mode="Markdown"
        )
        return

    # No active session - check for last ended session
    last_session = db.get_last_ended_session()

    if last_session:
        # Show last ended session summary
        ended_at = format_full_datetime(last_session.get('ended_at'))
        total_sales = last_session.get('total_sales', 0)
        order_count = db.get_order_count_by_session(last_session['id'])

        await query.edit_message_text(
            f"🏠 *Control Panel*\n\n"
            f"👋 Welcome back, {user_name}!\n\n"
            f"📊 *Last Session*\n"
            f"Ended: {ended_at}\n"
            f"💰 Total: ${total_sales:.2f} | 📝 Orders: {order_count}\n\n"
            "Ready to start a new session?",
            reply_markup=get_control_panel_keyboard(),
            parse_mode="Markdown"
        )
    else:
        # First time user - no sessions at all
        await query.edit_message_text(
            f"🏠 *Control Panel*\n\n"
            f"👋 Welcome to Kori POS, {user_name}!\n\n"
            "Ready to get started?\n"
            "Set up your menu and start your first session!",
            reply_markup=get_control_panel_keyboard(),
            parse_mode="Markdown"
        )


@require_auth
async def view_past_sales_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View past sales sessions"""
    query = update.callback_query
    await query.answer()

    # Check if there's an active session
    active_session = db.get_active_session()

    # Get page number from callback data if present
    page = 0
    if ':' in query.data:
        page = int(query.data.split(':')[1])

    # Pagination settings
    per_page = 10
    offset = page * per_page

    # Get past sessions
    sessions = db.get_past_sessions(limit=per_page, offset=offset)

    if not sessions:
        await query.edit_message_text(
            "📊 *Past Sales*\n\n"
            "No sales sessions found.",
            reply_markup=get_control_panel_keyboard(active_session),
            parse_mode="Markdown"
        )
        return

    # Format sessions list
    lines = ["📊 *Past Sales Sessions:*\n"]
    for session in sessions:
        started = format_full_datetime(session['started_at']) if session.get('started_at') else "N/A"

        if session['status'] == 'active':
            status = "🟢 Active"
            time_info = f"Started: {started}"
        else:
            status = "🔴 Ended"
            ended = format_full_datetime(session['ended_at']) if session.get('ended_at') else "N/A"
            time_info = f"Started: {started}\nEnded: {ended}"

        total = session.get('total_sales', 0)

        lines.append(
            f"{status}\n"
            f"{time_info}\n"
            f"Total: ${total:.2f}\n"
        )

    text = "\n".join(lines)

    # Calculate total pages (you'd need to query total count for accurate pagination)
    total_pages = page + 2 if len(sessions) == per_page else page + 1

    await query.edit_message_text(
        text,
        reply_markup=get_pagination_keyboard(page, total_pages, "view_sales", active_session),
        parse_mode="Markdown"
    )


@require_auth
async def view_past_inventory_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View past inventory logs with pagination"""
    query = update.callback_query
    await query.answer()

    # Check if there's an active session
    active_session = db.get_active_session()

    # Get page number from callback data if present
    page = 0
    if ':' in query.data:
        page = int(query.data.split(':')[1])

    # Pagination settings
    per_page = 5  # Reduced per page since we're showing detailed items
    offset = page * per_page

    # Get sessions with inventory
    sessions = db.get_sessions_with_inventory(limit=per_page, offset=offset)

    if not sessions:
        await query.edit_message_text(
            "📦 *Past Inventory*\n\n"
            "No inventory logs found.",
            reply_markup=get_control_panel_keyboard(active_session),
            parse_mode="Markdown"
        )
        return

    # Format sessions list with individual items
    lines = ["📦 *Past Inventory Sessions:*\n"]
    for session in sessions:
        started = format_full_datetime(session['started_at']) if session.get('started_at') else "N/A"

        if session['status'] == 'active':
            status = "🟢 Active"
            time_info = f"Started: {started}"
        else:
            status = "🔴 Ended"
            ended = format_full_datetime(session['ended_at']) if session.get('ended_at') else "N/A"
            time_info = f"Started: {started}\nEnded: {ended}"

        lines.append(f"{status}\n{time_info}")

        # Get and display individual inventory items
        inventory = db.get_inventory_by_session(session['id'])
        if inventory:
            lines.append(format_inventory_list(inventory))
        else:
            lines.append("No items logged")

        lines.append("")  # Add spacing between sessions

    text = "\n".join(lines)

    # Calculate total pages
    total_pages = page + 2 if len(sessions) == per_page else page + 1

    await query.edit_message_text(
        text,
        reply_markup=get_pagination_keyboard(page, total_pages, "view_inventory", active_session),
        parse_mode="Markdown"
    )
