-- Kaori POS Bot - Database Schema for Supabase
-- Run this script in your Supabase SQL Editor

-- Table 1: Authorized Users
CREATE TABLE IF NOT EXISTS authorized_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_id BIGINT UNIQUE NOT NULL,
    username TEXT,
    full_name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index on telegram_id for fast lookups
CREATE INDEX IF NOT EXISTS idx_authorized_users_telegram_id ON authorized_users(telegram_id);

-- Table 2: Menu Items
CREATE TABLE IF NOT EXISTS menu_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    size TEXT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    display_order INT DEFAULT 0,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for active menu items ordered by display_order
CREATE INDEX IF NOT EXISTS idx_menu_items_active ON menu_items(active, display_order);

-- Table 3: Sale Sessions
CREATE TABLE IF NOT EXISTS sale_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    started_by BIGINT NOT NULL,
    total_sales DECIMAL(10, 2) DEFAULT 0.00,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'ended')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for finding active sessions
CREATE INDEX IF NOT EXISTS idx_sale_sessions_status ON sale_sessions(status);

-- Index for session history by date
CREATE INDEX IF NOT EXISTS idx_sale_sessions_started_at ON sale_sessions(started_at DESC);

-- Table 4: Inventory Logs
CREATE TABLE IF NOT EXISTS inventory_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sale_sessions(id) ON DELETE CASCADE,
    item_name TEXT NOT NULL,
    quantity INT NOT NULL,
    cost_price DECIMAL(10, 2),
    logged_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for getting inventory by session
CREATE INDEX IF NOT EXISTS idx_inventory_logs_session_id ON inventory_logs(session_id);

-- Table 5: Orders
CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sale_sessions(id) ON DELETE CASCADE,
    order_number INT NOT NULL,
    items JSONB NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    payment_method TEXT NOT NULL CHECK (payment_method IN ('cash', 'paynow')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by BIGINT NOT NULL
);

-- Index for getting orders by session
CREATE INDEX IF NOT EXISTS idx_orders_session_id ON orders(session_id, order_number);

-- Index for orders by creation time
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at DESC);

-- Unique constraint for order_number per session
CREATE UNIQUE INDEX IF NOT EXISTS idx_orders_session_order_number ON orders(session_id, order_number);

-- Comments for documentation
COMMENT ON TABLE authorized_users IS 'Users authorized to access the POS bot';
COMMENT ON TABLE menu_items IS 'Menu items with sizes and prices';
COMMENT ON TABLE sale_sessions IS 'Sales sessions with start/end times and totals';
COMMENT ON TABLE inventory_logs IS 'Inventory entries logged at the start of each session';
COMMENT ON TABLE orders IS 'Individual orders placed during sale sessions';

COMMENT ON COLUMN authorized_users.telegram_id IS 'Unique Telegram user ID for authentication';
COMMENT ON COLUMN menu_items.display_order IS 'Order in which items appear in menus';
COMMENT ON COLUMN sale_sessions.status IS 'Session status: active or ended';
COMMENT ON COLUMN orders.items IS 'JSONB array of order items with quantities';
COMMENT ON COLUMN orders.order_number IS 'Incremental order number per session';

-- Sample data: Insert your authorized Telegram ID here
-- Replace 123456789 with your actual Telegram ID
-- You can get your Telegram ID from @userinfobot

-- INSERT INTO authorized_users (telegram_id, username, full_name)
-- VALUES (123456789, 'your_username', 'Your Full Name');

-- Function to get next order number for a session
CREATE OR REPLACE FUNCTION get_next_order_number(p_session_id UUID)
RETURNS INT AS $$
DECLARE
    next_number INT;
BEGIN
    SELECT COALESCE(MAX(order_number), 0) + 1
    INTO next_number
    FROM orders
    WHERE session_id = p_session_id;

    RETURN next_number;
END;
$$ LANGUAGE plpgsql;

-- Function to update session total when orders change
CREATE OR REPLACE FUNCTION update_session_total()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        UPDATE sale_sessions
        SET total_sales = (
            SELECT COALESCE(SUM(total_amount), 0)
            FROM orders
            WHERE session_id = OLD.session_id
        )
        WHERE id = OLD.session_id;
        RETURN OLD;
    ELSE
        UPDATE sale_sessions
        SET total_sales = (
            SELECT COALESCE(SUM(total_amount), 0)
            FROM orders
            WHERE session_id = NEW.session_id
        )
        WHERE id = NEW.session_id;
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update session total when orders are added/removed
CREATE TRIGGER trigger_update_session_total
AFTER INSERT OR DELETE ON orders
FOR EACH ROW
EXECUTE FUNCTION update_session_total();

-- Grant permissions (adjust based on your Supabase setup)
-- These are typically handled by Supabase RLS policies, but included for completeness

-- SELECT 'Schema created successfully!' AS status;
