"""
Database models and query functions for Supabase
"""
from typing import List, Dict, Optional, Any
from datetime import datetime
from .supabase_client import get_supabase_client


class Database:
    """Database operations wrapper"""

    def __init__(self):
        self.client = get_supabase_client()

    # ===== AUTHENTICATION =====

    def is_user_authorized(self, telegram_id: int) -> bool:
        """Check if a user is authorized to use the bot"""
        try:
            response = self.client.table("authorized_users").select("id").eq("telegram_id", telegram_id).execute()
            return len(response.data) > 0
        except Exception:
            return False

    def update_user_info(self, telegram_id: int, username: str = None, full_name: str = None):
        """Update user information"""
        try:
            data = {}
            if username:
                data["username"] = username
            if full_name:
                data["full_name"] = full_name

            if data:
                self.client.table("authorized_users").update(data).eq("telegram_id", telegram_id).execute()
        except Exception:
            pass

    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict]:
        """Get user information by telegram ID"""
        try:
            response = self.client.table("authorized_users").select("*").eq("telegram_id", telegram_id).execute()
            return response.data[0] if response.data else None
        except Exception:
            return None

    def get_all_authorized_users(self) -> List[Dict]:
        """Get all authorized users"""
        try:
            response = self.client.table("authorized_users").select("*").order("created_at", desc=True).execute()
            return response.data
        except Exception:
            return []

    def add_authorized_user(self, telegram_id: int, username: str = None, full_name: str = None) -> bool:
        """Add a new authorized user"""
        try:
            data = {
                "telegram_id": telegram_id,
                "username": username,
                "full_name": full_name
            }
            self.client.table("authorized_users").insert(data).execute()
            return True
        except Exception:
            return False

    def delete_authorized_user(self, telegram_id: int) -> bool:
        """Delete an authorized user"""
        try:
            self.client.table("authorized_users").delete().eq("telegram_id", telegram_id).execute()
            return True
        except Exception:
            return False

    # ===== MENU ITEMS =====

    def get_menu_items(self, active_only: bool = True) -> List[Dict]:
        """Get all menu items"""
        try:
            query = self.client.table("menu_items").select("*")
            if active_only:
                query = query.eq("active", True)
            response = query.order("display_order").execute()
            return response.data
        except Exception:
            return []

    def add_menu_item(self, name: str, size: str, price: float) -> Optional[Dict]:
        """Add a new menu item"""
        try:
            # Get the next display order
            max_order_response = self.client.table("menu_items").select("display_order").order("display_order", desc=True).limit(1).execute()
            next_order = (max_order_response.data[0]["display_order"] + 1) if max_order_response.data else 0

            response = self.client.table("menu_items").insert({
                "name": name,
                "size": size,
                "price": price,
                "display_order": next_order
            }).execute()
            return response.data[0] if response.data else None
        except Exception:
            return None

    def update_menu_item_name(self, item_id: str, name: str) -> bool:
        """Update the name of a menu item"""
        try:
            self.client.table("menu_items").update({"name": name}).eq("id", item_id).execute()
            return True
        except Exception:
            return False

    def update_menu_item_size(self, item_id: str, size: str) -> bool:
        """Update the size of a menu item"""
        try:
            self.client.table("menu_items").update({"size": size}).eq("id", item_id).execute()
            return True
        except Exception:
            return False

    def update_menu_item_price(self, item_id: str, price: float) -> bool:
        """Update the price of a menu item"""
        try:
            self.client.table("menu_items").update({"price": price}).eq("id", item_id).execute()
            return True
        except Exception:
            return False

    def delete_menu_item(self, item_id: str) -> bool:
        """Soft delete a menu item"""
        try:
            self.client.table("menu_items").update({"active": False}).eq("id", item_id).execute()
            return True
        except Exception:
            return False

    # ===== SALE SESSIONS =====

    def create_session(self, telegram_id: int) -> Optional[Dict]:
        """Create a new sale session"""
        try:
            response = self.client.table("sale_sessions").insert({
                "started_by": telegram_id,
                "status": "active"
            }).execute()
            return response.data[0] if response.data else None
        except Exception:
            return None

    def get_active_session(self) -> Optional[Dict]:
        """Get the currently active session"""
        try:
            response = self.client.table("sale_sessions").select("*").eq("status", "active").execute()
            return response.data[0] if response.data else None
        except Exception:
            return None

    def get_last_ended_session(self) -> Optional[Dict]:
        """Get the most recently ended session"""
        try:
            response = self.client.table("sale_sessions").select("*").eq("status", "ended").order("ended_at", desc=True).limit(1).execute()
            return response.data[0] if response.data else None
        except Exception:
            return None

    def end_session(self, session_id: str) -> bool:
        """End a sale session"""
        try:
            self.client.table("sale_sessions").update({
                "status": "ended",
                "ended_at": datetime.utcnow().isoformat()
            }).eq("id", session_id).execute()
            return True
        except Exception:
            return False

    def get_session_by_id(self, session_id: str) -> Optional[Dict]:
        """Get a session by ID"""
        try:
            response = self.client.table("sale_sessions").select("*").eq("id", session_id).execute()
            return response.data[0] if response.data else None
        except Exception:
            return None

    def get_past_sessions(self, limit: int = 10, offset: int = 0) -> List[Dict]:
        """Get past sessions with pagination"""
        try:
            response = self.client.table("sale_sessions").select("*").order("started_at", desc=True).range(offset, offset + limit - 1).execute()
            return response.data
        except Exception:
            return []

    # ===== INVENTORY LOGS =====

    def add_inventory_log(self, session_id: str, item_name: str, quantity: int, cost_price: Optional[float] = None) -> Optional[Dict]:
        """Add an inventory log entry"""
        try:
            data = {
                "session_id": session_id,
                "item_name": item_name,
                "quantity": quantity
            }
            if cost_price is not None:
                data["cost_price"] = cost_price

            response = self.client.table("inventory_logs").insert(data).execute()
            return response.data[0] if response.data else None
        except Exception:
            return None

    def get_inventory_by_session(self, session_id: str) -> List[Dict]:
        """Get all inventory logs for a session"""
        try:
            response = self.client.table("inventory_logs").select("*").eq("session_id", session_id).execute()
            return response.data
        except Exception:
            return []

    def get_sessions_with_inventory(self, limit: int = 10, offset: int = 0) -> List[Dict]:
        """Get sessions that have inventory logs with pagination"""
        try:
            # Get all sessions with inventory, ordered by started_at descending
            response = self.client.table("sale_sessions").select(
                "id, started_at, ended_at, started_by, status"
            ).order("started_at", desc=True).range(offset, offset + limit - 1).execute()

            # Filter sessions that have inventory
            sessions_with_inventory = []
            for session in response.data:
                inventory = self.get_inventory_by_session(session['id'])
                if inventory:
                    session['inventory_count'] = len(inventory)
                    sessions_with_inventory.append(session)

            return sessions_with_inventory
        except Exception:
            return []

    # ===== ORDERS =====

    def create_order(self, session_id: str, items: List[Dict], payment_method: str, telegram_id: int) -> Optional[Dict]:
        """Create a new order"""
        try:
            # Calculate total
            total = sum(item["price"] * item["quantity"] for item in items)

            # Get next order number using RPC function
            response = self.client.rpc("get_next_order_number", {"p_session_id": session_id}).execute()
            order_number = response.data

            # Create order
            order_response = self.client.table("orders").insert({
                "session_id": session_id,
                "order_number": order_number,
                "items": items,
                "total_amount": total,
                "payment_method": payment_method,
                "created_by": telegram_id
            }).execute()

            return order_response.data[0] if order_response.data else None
        except Exception:
            return None

    def get_orders_by_session(self, session_id: str, limit: int = 10, offset: int = 0) -> List[Dict]:
        """Get orders for a session with pagination"""
        try:
            response = self.client.table("orders").select("*").eq("session_id", session_id).order("order_number", desc=False).range(offset, offset + limit - 1).execute()
            return response.data
        except Exception:
            return []

    def get_order_by_id(self, order_id: str) -> Optional[Dict]:
        """Get an order by ID"""
        try:
            response = self.client.table("orders").select("*").eq("id", order_id).execute()
            return response.data[0] if response.data else None
        except Exception:
            return None

    def delete_order(self, order_id: str) -> bool:
        """Delete an order"""
        try:
            self.client.table("orders").delete().eq("id", order_id).execute()
            return True
        except Exception:
            return False

    def get_order_count_by_session(self, session_id: str) -> int:
        """Get total number of orders in a session"""
        try:
            response = self.client.table("orders").select("id", count="exact").eq("session_id", session_id).execute()
            return response.count if response.count else 0
        except Exception:
            return 0
