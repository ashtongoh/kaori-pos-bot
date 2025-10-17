"""
Control panel handlers
"""
from telegram import Update
from telegram.ext import ContextTypes
from src.bot.middleware import require_auth
from src.database.models import Database
from src.bot.keyboards import get_control_panel_keyboard, get_pagination_keyboard
from src.utils.formatters import format_session_summary, format_inventory_list
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
        # Redirect to sales dashboard
        from src.bot.handlers.sales import show_sales_dashboard
        return await show_sales_dashboard(update, context)

    # Show control panel
    await update.message.reply_text(
        f"👋 Welcome to Kaori POS, {user.first_name}!\n\n"
        "Use the buttons below to manage your business:",
        reply_markup=get_control_panel_keyboard()
    )


@require_auth
async def control_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show control panel"""
    query = update.callback_query
    await query.answer()

    # Check if there's an active session
    active_session = db.get_active_session()

    if active_session:
        await query.edit_message_text(
            "⚠️ You have an active sale session.\n\n"
            "Please end the current session before accessing the control panel.",
            reply_markup=get_control_panel_keyboard()
        )
        return

    await query.edit_message_text(
        "🏠 *Control Panel*\n\n"
        "Choose an option:",
        reply_markup=get_control_panel_keyboard(),
        parse_mode="Markdown"
    )


@require_auth
async def view_past_sales_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View past sales sessions"""
    query = update.callback_query
    await query.answer()

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
            reply_markup=get_control_panel_keyboard(),
            parse_mode="Markdown"
        )
        return

    # Format sessions list
    lines = ["📊 *Past Sales Sessions:*\n"]
    for session in sessions:
        started = format_full_datetime(session['started_at']) if session.get('started_at') else "N/A"
        status = "🟢 Active" if session['status'] == 'active' else "⚪ Ended"
        total = session.get('total_sales', 0)

        lines.append(
            f"{status}\n"
            f"Started: {started}\n"
            f"Total: ${total:.2f}\n"
        )

    text = "\n".join(lines)

    # Calculate total pages (you'd need to query total count for accurate pagination)
    total_pages = page + 2 if len(sessions) == per_page else page + 1

    await query.edit_message_text(
        text,
        reply_markup=get_pagination_keyboard(page, total_pages, "view_sales"),
        parse_mode="Markdown"
    )


@require_auth
async def view_past_inventory_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View past inventory logs"""
    query = update.callback_query
    await query.answer()

    # Get the most recent session
    sessions = db.get_past_sessions(limit=1)

    if not sessions:
        await query.edit_message_text(
            "📦 *Past Inventory*\n\n"
            "No inventory logs found.",
            reply_markup=get_control_panel_keyboard(),
            parse_mode="Markdown"
        )
        return

    recent_session = sessions[0]
    inventory = db.get_inventory_by_session(recent_session['id'])

    if not inventory:
        await query.edit_message_text(
            "📦 *Past Inventory*\n\n"
            f"Session: {format_full_datetime(recent_session['started_at'])}\n\n"
            "No inventory logged for this session.",
            reply_markup=get_control_panel_keyboard(),
            parse_mode="Markdown"
        )
        return

    text = (
        f"📦 *Past Inventory*\n\n"
        f"Session: {format_full_datetime(recent_session['started_at'])}\n\n"
        f"{format_inventory_list(inventory)}"
    )

    await query.edit_message_text(
        text,
        reply_markup=get_control_panel_keyboard(),
        parse_mode="Markdown"
    )
