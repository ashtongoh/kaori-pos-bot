"""
Message formatting utilities
"""
from typing import List, Dict


def format_currency(amount: float) -> str:
    """
    Format currency amount in SGD

    Args:
        amount: Amount to format

    Returns:
        str: Formatted currency string (e.g., "$12.50")
    """
    return f"${amount:.2f}"


def format_menu_item(item: Dict) -> str:
    """
    Format a single menu item for display

    Args:
        item: Menu item dictionary

    Returns:
        str: Formatted menu item string
    """
    return f"{item['name']} ({item['size']}) - {format_currency(item['price'])}"


def format_menu_list(items: List[Dict]) -> str:
    """
    Format a list of menu items

    Args:
        items: List of menu item dictionaries

    Returns:
        str: Formatted menu list
    """
    if not items:
        return "No menu items found."

    lines = ["📋 *Current Menu:*\n"]
    for i, item in enumerate(items, 1):
        lines.append(f"{i}. {format_menu_item(item)}")

    return "\n".join(lines)


def format_cart(cart: Dict) -> str:
    """
    Format shopping cart for display

    Args:
        cart: Cart dictionary {item_id: {name, size, price, quantity}}

    Returns:
        str: Formatted cart string
    """
    if not cart:
        return "🛒 *Cart is empty*"

    lines = ["🛒 *Current Cart:*\n"]
    subtotal = 0

    for item_id, item in cart.items():
        item_total = item['price'] * item['quantity']
        subtotal += item_total
        lines.append(f"• {item['name']} ({item['size']}) x{item['quantity']} = {format_currency(item_total)}")

    lines.append(f"\n*Subtotal:* {format_currency(subtotal)}")
    return "\n".join(lines)


def format_order_items(items: List[Dict]) -> str:
    """
    Format order items for display

    Args:
        items: List of order items

    Returns:
        str: Formatted items string
    """
    lines = []
    for item in items:
        qty = item.get('quantity', 1)
        item_total = item['price'] * qty
        lines.append(f"• {item['name']} ({item['size']}) x{qty} = {format_currency(item_total)}")

    return "\n".join(lines)


def format_order_summary(order: Dict) -> str:
    """
    Format a complete order summary

    Args:
        order: Order dictionary

    Returns:
        str: Formatted order summary
    """
    lines = [
        f"📝 *Order #{order['order_number']}*\n",
        format_order_items(order['items']),
        f"\n*Total:* {format_currency(order['total_amount'])}",
        f"*Payment:* {order['payment_method'].title()}"
    ]

    return "\n".join(lines)


def format_session_summary(session: Dict, order_count: int, items_sold: Dict = None) -> str:
    """
    Format session summary

    Args:
        session: Session dictionary
        order_count: Number of orders in session
        items_sold: Optional dictionary of items sold {item_name: quantity}

    Returns:
        str: Formatted session summary
    """
    lines = [
        "📊 *Session Summary*\n",
        f"*Total Orders:* {order_count}",
        f"*Total Revenue:* {format_currency(session.get('total_sales', 0))}"
    ]

    if items_sold:
        lines.append("\n*Items Sold:*")
        for item_name, qty in items_sold.items():
            lines.append(f"• {item_name}: {qty}")

    return "\n".join(lines)


def format_inventory_list(inventory: List[Dict]) -> str:
    """
    Format inventory list

    Args:
        inventory: List of inventory log dictionaries

    Returns:
        str: Formatted inventory list
    """
    if not inventory:
        return "No inventory logged."

    lines = ["📦 *Starting Inventory:*\n"]
    for item in inventory:
        line = f"• {item['item_name']}: {item['quantity']}"
        if item.get('cost_price'):
            line += f" @ {format_currency(item['cost_price'])}"
        lines.append(line)

    return "\n".join(lines)
