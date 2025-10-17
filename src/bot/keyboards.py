"""
Inline keyboard layouts for the bot
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Dict


def get_control_panel_keyboard(active_session=None) -> InlineKeyboardMarkup:
    """Get the main control panel keyboard"""
    keyboard = []

    if active_session:
        # Show "Join Session" button if there's an active session
        keyboard.append([InlineKeyboardButton("📱 Join Active Session", callback_data="join_session")])
    else:
        # Show "Start Session" button if no active session
        keyboard.append([InlineKeyboardButton("🟢 Start Session", callback_data="start_session")])

    keyboard.extend([
        [InlineKeyboardButton("📊 View Past Sales", callback_data="view_sales")],
        [InlineKeyboardButton("📦 View Past Inventory", callback_data="view_inventory")],
        [InlineKeyboardButton("📋 Manage Menu", callback_data="manage_menu")]
    ])
    return InlineKeyboardMarkup(keyboard)


def get_sales_dashboard_keyboard(total_sales: float) -> InlineKeyboardMarkup:
    """
    Get the active sales dashboard keyboard

    Args:
        total_sales: Current session total sales
    """
    keyboard = [
        [
            InlineKeyboardButton("🔄 Refresh", callback_data="refresh_dashboard"),
            InlineKeyboardButton("➕ New Order", callback_data="new_order")
        ],
        [InlineKeyboardButton("📝 View Orders", callback_data="view_orders")],
        [InlineKeyboardButton("🔴 End Session", callback_data="end_session")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_menu_items_keyboard(menu_items: List[Dict], cart: Dict = None) -> InlineKeyboardMarkup:
    """
    Get keyboard with menu items for ordering in grid layout
    Format: [Item Name] [Size 1] [Size 2] [Size 3]

    Args:
        menu_items: List of menu item dictionaries
        cart: Optional cart dictionary to show selected items
    """
    keyboard = []

    # Group items by name
    items_by_name = {}
    for item in menu_items:
        name = item['name']
        if name not in items_by_name:
            items_by_name[name] = []
        items_by_name[name].append(item)

    # Build grid layout
    for item_name, variants in items_by_name.items():
        row = []

        # Add item name button (non-clickable, just for display)
        row.append(InlineKeyboardButton(f"📦 {item_name}", callback_data="noop"))

        # Add size buttons
        for variant in sorted(variants, key=lambda x: x['price']):  # Sort by price
            qty_indicator = ""
            if cart and variant['id'] in cart:
                qty_indicator = f" ({cart[variant['id']]['quantity']})"

            button_text = f"{variant['size']} ${variant['price']:.2f}{qty_indicator}"
            row.append(InlineKeyboardButton(button_text, callback_data=f"add_item:{variant['id']}"))

        keyboard.append(row)

    # Add control buttons
    keyboard.append([
        InlineKeyboardButton("🗑 Clear Cart", callback_data="clear_cart"),
        InlineKeyboardButton("✅ Confirm", callback_data="confirm_cart")
    ])
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_order")])

    return InlineKeyboardMarkup(keyboard)


def get_payment_method_keyboard() -> InlineKeyboardMarkup:
    """Get payment method selection keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("💵 Cash", callback_data="payment:cash"),
            InlineKeyboardButton("📱 PayNow", callback_data="payment:paynow")
        ],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_payment")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_orders_list_keyboard(orders: List[Dict], page: int = 0, total_pages: int = 1) -> InlineKeyboardMarkup:
    """
    Get keyboard with list of orders

    Args:
        orders: List of order dictionaries
        page: Current page number (0-indexed)
        total_pages: Total number of pages
    """
    keyboard = []

    # Add order buttons
    for order in orders:
        button_text = f"Order #{order['order_number']} - ${order['total_amount']:.2f}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"view_order:{order['id']}")])

    # Add pagination if needed
    if total_pages > 1:
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"orders_page:{page - 1}"))
        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"orders_page:{page + 1}"))
        if nav_row:
            keyboard.append(nav_row)

    # Add back button
    keyboard.append([InlineKeyboardButton("🔙 Back to Dashboard", callback_data="back_to_dashboard")])

    return InlineKeyboardMarkup(keyboard)


def get_order_detail_keyboard(order_id: str) -> InlineKeyboardMarkup:
    """
    Get keyboard for order detail view

    Args:
        order_id: Order ID
    """
    keyboard = [
        [InlineKeyboardButton("🗑 Delete Order", callback_data=f"delete_order:{order_id}")],
        [InlineKeyboardButton("🔙 Back to Orders", callback_data="view_orders")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_confirm_delete_keyboard(order_id: str) -> InlineKeyboardMarkup:
    """
    Get confirmation keyboard for deleting an order

    Args:
        order_id: Order ID to delete
    """
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes, Delete", callback_data=f"confirm_delete:{order_id}"),
            InlineKeyboardButton("❌ No, Cancel", callback_data=f"view_order:{order_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_confirm_end_session_keyboard() -> InlineKeyboardMarkup:
    """Get confirmation keyboard for ending session"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes, End Session", callback_data="confirm_end_session"),
            InlineKeyboardButton("❌ No, Go Back", callback_data="back_to_dashboard")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_menu_management_keyboard(menu_items: List[Dict]) -> InlineKeyboardMarkup:
    """
    Get keyboard for menu management

    Args:
        menu_items: List of menu item dictionaries
    """
    keyboard = []

    # Add menu items for editing/deletion
    for item in menu_items:
        button_text = f"{item['name']} ({item['size']}) - ${item['price']:.2f}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"edit_menu_item:{item['id']}")])

    # Add control buttons
    keyboard.append([InlineKeyboardButton("➕ Add New Item", callback_data="add_menu_item")])
    keyboard.append([InlineKeyboardButton("🔙 Back to Control Panel", callback_data="control_panel")])

    return InlineKeyboardMarkup(keyboard)


def get_pagination_keyboard(page: int, total_pages: int, prefix: str, active_session=None) -> InlineKeyboardMarkup:
    """
    Generic pagination keyboard

    Args:
        page: Current page (0-indexed)
        total_pages: Total number of pages
        prefix: Callback data prefix (e.g., "view_sales", "view_inventory")
        active_session: Optional active session dict to maintain context
    """
    keyboard = []
    nav_row = []

    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"{prefix}:{page - 1}"))

    nav_row.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="noop"))

    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"{prefix}:{page + 1}"))

    if nav_row:
        keyboard.append(nav_row)

    # Show appropriate back button based on active session
    if active_session:
        keyboard.append([InlineKeyboardButton("🔙 Back to Control Panel", callback_data="control_panel")])
    else:
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="control_panel")])

    return InlineKeyboardMarkup(keyboard)


def get_back_button() -> InlineKeyboardMarkup:
    """Simple back to control panel button"""
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Control Panel", callback_data="control_panel")]])


def get_cancel_button() -> InlineKeyboardMarkup:
    """Cancel button for conversation handlers"""
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_menu_setup")]])


def get_add_another_menu_item_keyboard() -> InlineKeyboardMarkup:
    """Keyboard after adding a menu item"""
    keyboard = [
        [InlineKeyboardButton("➕ Add Another Item", callback_data="add_menu_item")],
        [InlineKeyboardButton("📋 View Menu", callback_data="manage_menu")],
        [InlineKeyboardButton("🔙 Back to Control Panel", callback_data="control_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_yes_no_keyboard(yes_callback: str, no_callback: str) -> InlineKeyboardMarkup:
    """Generic yes/no keyboard with custom callbacks"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes", callback_data=yes_callback),
            InlineKeyboardButton("❌ No", callback_data=no_callback)
        ],
        [InlineKeyboardButton("🔙 Cancel", callback_data="cancel_menu_setup")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_edit_menu_item_keyboard(item_id: str) -> InlineKeyboardMarkup:
    """Keyboard for editing a specific menu item"""
    keyboard = [
        [InlineKeyboardButton("📝 Edit Name", callback_data=f"edit_name:{item_id}")],
        [InlineKeyboardButton("📏 Edit Size", callback_data=f"edit_size:{item_id}")],
        [InlineKeyboardButton("💰 Edit Price", callback_data=f"edit_price:{item_id}")],
        [InlineKeyboardButton("🗑 Delete Item", callback_data=f"confirm_delete_menu_item:{item_id}")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="manage_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_confirm_delete_menu_item_keyboard(item_id: str) -> InlineKeyboardMarkup:
    """Keyboard for confirming menu item deletion"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes, Delete", callback_data=f"delete_menu_item:{item_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"edit_menu_item:{item_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Back to menu management button"""
    keyboard = [
        [InlineKeyboardButton("📋 Back to Menu", callback_data="manage_menu")],
        [InlineKeyboardButton("🔙 Back to Control Panel", callback_data="control_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_skip_inventory_keyboard() -> InlineKeyboardMarkup:
    """Skip button for inventory input"""
    keyboard = [
        [InlineKeyboardButton("⏭ Skip Inventory", callback_data="skip_inventory")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_inventory_start_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for starting inventory input with cancel option"""
    keyboard = [
        [InlineKeyboardButton("📦 Start Adding Inventory", callback_data="start_adding_inventory")],
        [InlineKeyboardButton("⏭ Skip Inventory", callback_data="skip_inventory")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_session_start")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_add_another_inventory_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for asking if user wants to add another inventory item"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes", callback_data="add_another_inventory:yes"),
            InlineKeyboardButton("❌ No", callback_data="add_another_inventory:no")
        ],
        [InlineKeyboardButton("🔙 Cancel", callback_data="cancel_session_start")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_inventory_skip_price_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for skipping cost price during inventory input"""
    keyboard = [
        [InlineKeyboardButton("⏭ Skip Cost Price", callback_data="skip_inventory_price")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_session_start")]
    ]
    return InlineKeyboardMarkup(keyboard)
