"""
User management handlers - Manual state management
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError
from src.bot.middleware import require_auth, require_auth_callback
from src.database.models import Database
from src.bot.keyboards import (
    get_user_management_keyboard,
    get_add_user_keyboard,
    get_confirm_add_user_keyboard,
    get_confirm_delete_user_keyboard,
    get_control_panel_keyboard
)
from src.utils.formatters import format_user_display_name

db = Database()
logger = logging.getLogger(__name__)


@require_auth_callback
async def manage_users_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of authorized users"""
    # Note: query.answer() is already called by @require_auth_callback middleware
    query = update.callback_query

    # Get all authorized users
    users = db.get_all_authorized_users()

    if not users:
        await query.edit_message_text(
            "👥 *Manage Users*\n\n"
            "No authorized users found.\n\n"
            "Click 'Add User' to authorize someone:",
            reply_markup=get_user_management_keyboard([]),
            parse_mode="Markdown"
        )
        return

    # Format user list
    user_count = len(users)
    text = f"👥 *Manage Users* ({user_count} total)\n\n" \
           f"Select a user to remove, or add a new user:"

    await query.edit_message_text(
        text,
        reply_markup=get_user_management_keyboard(users),
        parse_mode="Markdown"
    )


@require_auth_callback
async def add_user_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the add user flow"""
    # Note: query.answer() is already called by @require_auth_callback middleware
    query = update.callback_query

    # Set state
    context.user_data['user_mgmt_state'] = 'AWAITING_TELEGRAM_ID'

    await query.edit_message_text(
        "➕ *Add Authorized User*\n\n"
        "Please enter the Telegram ID of the user you want to authorize:\n\n"
        "_You can get a user's Telegram ID by asking them to message @userinfobot_",
        reply_markup=get_add_user_keyboard(),
        parse_mode="Markdown"
    )


@require_auth_callback
async def cancel_user_mgmt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel user management and return to user list"""
    # Note: query.answer() is already called by @require_auth_callback middleware
    query = update.callback_query

    # Clear state
    context.user_data.pop('user_mgmt_state', None)
    context.user_data.pop('pending_user_data', None)

    # Get all authorized users
    users = db.get_all_authorized_users()

    if not users:
        await query.edit_message_text(
            "👥 *Manage Users*\n\n"
            "No authorized users found.\n\n"
            "Click 'Add User' to authorize someone:",
            reply_markup=get_user_management_keyboard([]),
            parse_mode="Markdown"
        )
        return

    # Format user list
    user_count = len(users)
    text = f"👥 *Manage Users* ({user_count} total)\n\n" \
           f"Select a user to remove, or add a new user:"

    await query.edit_message_text(
        text,
        reply_markup=get_user_management_keyboard(users),
        parse_mode="Markdown"
    )


@require_auth
async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages during user management flow"""
    state = context.user_data.get('user_mgmt_state')

    if not state:
        return  # Not in user management flow, ignore

    if state == 'AWAITING_TELEGRAM_ID':
        await receive_telegram_id(update, context)


async def receive_telegram_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive and validate telegram ID"""
    telegram_id_text = update.message.text.strip()

    # Validate it's a number
    try:
        telegram_id = int(telegram_id_text)
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid Telegram ID. Please enter a valid number:",
            reply_markup=get_add_user_keyboard(),
            parse_mode="Markdown"
        )
        return

    # Check if user already exists
    existing_user = db.get_user_by_telegram_id(telegram_id)
    if existing_user:
        await update.message.reply_text(
            f"⚠️ This user is already authorized!\n\n"
            f"User: {format_user_display_name(telegram_id, existing_user.get('full_name'))}\n\n"
            "Please enter a different Telegram ID:",
            reply_markup=get_add_user_keyboard(),
            parse_mode="Markdown"
        )
        return

    # Try to fetch user info from Telegram
    try:
        chat = await context.bot.get_chat(telegram_id)

        # Build full name
        full_name_parts = []
        if chat.first_name:
            full_name_parts.append(chat.first_name)
        if chat.last_name:
            full_name_parts.append(chat.last_name)
        full_name = " ".join(full_name_parts) if full_name_parts else None

        username = chat.username

        # Store user data temporarily
        context.user_data['pending_user_data'] = {
            'telegram_id': telegram_id,
            'username': username,
            'full_name': full_name,
            'first_name': chat.first_name
        }

        # Clear state
        context.user_data['user_mgmt_state'] = None

        # Show confirmation
        display_name = full_name if full_name else f"User ID {telegram_id}"
        username_text = f"@{username}" if username else "No username"

        await update.message.reply_text(
            f"👤 *Add this user?*\n\n"
            f"Name: {display_name}\n"
            f"Username: {username_text}\n"
            f"Telegram ID: `{telegram_id}`\n\n"
            "Confirm to authorize this user:",
            reply_markup=get_confirm_add_user_keyboard(telegram_id),
            parse_mode="Markdown"
        )

    except TelegramError as e:
        logger.error(f"Error fetching user info for {telegram_id}: {e}")
        await update.message.reply_text(
            f"⚠️ Could not fetch user information for ID: {telegram_id}\n\n"
            "This could mean:\n"
            "• The user hasn't started the bot yet\n"
            "• The ID is invalid\n"
            "• The user has blocked the bot\n\n"
            "You can still add them, but their name won't be populated until they interact with the bot.\n\n"
            "Try a different ID or cancel:",
            reply_markup=get_add_user_keyboard(),
            parse_mode="Markdown"
        )


@require_auth_callback
async def confirm_add_user_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and add the user"""
    # Note: query.answer() is already called by @require_auth_callback middleware
    query = update.callback_query

    # Get pending user data
    user_data = context.user_data.get('pending_user_data')
    if not user_data:
        await query.edit_message_text(
            "❌ Error: User data not found. Please try again.",
            reply_markup=get_user_management_keyboard(db.get_all_authorized_users())
        )
        return

    telegram_id = user_data['telegram_id']
    username = user_data.get('username')
    full_name = user_data.get('full_name')

    # Add user to database
    success = db.add_authorized_user(telegram_id, username, full_name)

    # Clear pending data
    context.user_data.pop('pending_user_data', None)

    if success:
        display_name = full_name if full_name else f"User ID {telegram_id}"
        await query.edit_message_text(
            f"✅ *User Authorized!*\n\n"
            f"{display_name} can now use the bot.\n\n"
            "Returning to user management...",
            parse_mode="Markdown"
        )

        # Wait a moment then show user list
        import asyncio
        await asyncio.sleep(1.5)
        users = db.get_all_authorized_users()
        await query.edit_message_text(
            f"👥 *Manage Users* ({len(users)} total)\n\n"
            "Select a user to remove, or add a new user:",
            reply_markup=get_user_management_keyboard(users),
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text(
            "❌ Failed to authorize user. Please try again.",
            reply_markup=get_user_management_keyboard(db.get_all_authorized_users())
        )


@require_auth_callback
async def delete_user_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show confirmation to delete user"""
    # Note: query.answer() is already called by @require_auth_callback middleware
    query = update.callback_query

    # Extract telegram ID from callback data
    telegram_id = int(query.data.split(':')[1])

    # Get user info
    user = db.get_user_by_telegram_id(telegram_id)
    if not user:
        await query.edit_message_text(
            "❌ User not found.",
            reply_markup=get_user_management_keyboard(db.get_all_authorized_users())
        )
        return

    display_name = format_user_display_name(telegram_id, user.get('full_name'))

    await query.edit_message_text(
        f"⚠️ *Remove User Authorization?*\n\n"
        f"User: {display_name}\n"
        f"Telegram ID: `{telegram_id}`\n\n"
        "This user will immediately lose access to the bot.\n\n"
        "Are you sure?",
        reply_markup=get_confirm_delete_user_keyboard(telegram_id),
        parse_mode="Markdown"
    )


@require_auth_callback
async def confirm_delete_user_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and delete the user"""
    # Note: query.answer() is already called by @require_auth_callback middleware
    query = update.callback_query

    # Extract telegram ID from callback data
    telegram_id = int(query.data.split(':')[1])

    # Get user info before deletion
    user = db.get_user_by_telegram_id(telegram_id)
    if not user:
        await query.edit_message_text(
            "❌ User not found.",
            reply_markup=get_user_management_keyboard(db.get_all_authorized_users())
        )
        return

    display_name = format_user_display_name(telegram_id, user.get('full_name'))

    # Delete user
    success = db.delete_authorized_user(telegram_id)

    if success:
        await query.edit_message_text(
            f"✅ *User Removed*\n\n"
            f"{display_name} has been removed from authorized users.\n\n"
            "Returning to user management...",
            parse_mode="Markdown"
        )

        # Wait a moment then show user list
        import asyncio
        await asyncio.sleep(1.5)
        users = db.get_all_authorized_users()
        await query.edit_message_text(
            f"👥 *Manage Users* ({len(users)} total)\n\n"
            "Select a user to remove, or add a new user:",
            reply_markup=get_user_management_keyboard(users),
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text(
            "❌ Failed to remove user. Please try again.",
            reply_markup=get_user_management_keyboard(db.get_all_authorized_users())
        )
