# Kaori POS Bot - Project Documentation

## Project Overview
A Telegram bot-based Point of Sale (POS) system for merchants to manage sales, inventory, and orders through a user-friendly chat interface.

## Key Features

### 1. Menu Management
- Setup menu items with name and size variations (e.g., "Hojicha: Reg, Large")
- Each size variation is a separate menu item for quick ordering
- Edit and delete menu items as needed

### 2. Central Control Panel
- View past sales sessions
- View past inventory logs
- Start new sale session
- All timestamps in Singapore Time (SGT)

### 3. Inventory Management
- Pre-session inventory input (item name, quantity, optional cost price)
- Record-keeping for forecasting future inventory needs
- Inventory logs tied to specific sale sessions

### 4. Active Sale Session
- **Real-time sales dashboard** showing current session total
- **New Order**:
  - Click-to-add menu interface with inline keyboard
  - Running cart display above menu buttons
  - Payment method selection (Cash/PayNow)
  - Confirm order button
- **View Orders**:
  - Paginated list of all orders in current session
  - Click to view order details
  - Delete order functionality (with confirmation)
- **End Session**:
  - Double confirmation with timestamp
  - Sales summary (items sold, total revenue, order count)
  - Return to control panel

### 5. Authentication
- Telegram ID-based authentication
- Authorized user IDs hardcoded in database
- Multiple staff can use the same bot instance

### 6. Data Persistence
- All past sessions viewable indefinitely
- Complete order history maintained

## Technical Stack

### Backend
- **Language**: Python 3.10+
- **Bot Framework**: python-telegram-bot (v20.7) with webhook mode
- **Database**: Supabase (PostgreSQL)
- **Timezone**: pytz with 'Asia/Singapore'
- **Web Server**: Flask/FastAPI for webhook endpoint
- **Deployment**: Digital Ocean with HTTPS/SSL

### Dependencies
```
python-telegram-bot[webhooks]==20.7
supabase==2.3.0
pytz==2024.1
python-dotenv==1.0.0
flask==3.0.0
```

## Project Structure
```
kaori-pos-bot/
├── src/
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── handlers/
│   │   │   ├── __init__.py
│   │   │   ├── setup.py          # Menu setup handlers
│   │   │   ├── control_panel.py  # Main control panel
│   │   │   ├── inventory.py      # Inventory input handlers
│   │   │   ├── sales.py          # Active sale session handlers
│   │   │   └── orders.py         # Order management
│   │   ├── keyboards.py          # Inline keyboard layouts
│   │   └── middleware.py         # Auth middleware
│   ├── database/
│   │   ├── __init__.py
│   │   ├── supabase_client.py    # Supabase connection
│   │   └── models.py             # Data models/queries
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── timezone.py           # Singapore timezone utilities
│   │   └── formatters.py         # Message formatting helpers
│   └── main.py                   # Bot entry point & webhook setup
├── migrations/
│   └── supabase_schema.sql       # Database schema
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── claude.md                     # This file
```

## Database Schema

### 1. authorized_users
- `id` (uuid, primary key)
- `telegram_id` (bigint, unique, NOT NULL) - Used for authentication
- `username` (text, nullable) - For display/reference only
- `full_name` (text, nullable) - For display/reference only
- `created_at` (timestamptz)

**Authentication**: Only `telegram_id` is checked. Username is optional and for display purposes only.

### 2. menu_items
- `id` (uuid, primary key)
- `name` (text) - Item name with size (e.g., "Hojicha: Reg")
- `size` (text) - Size variant (e.g., "Reg", "Large")
- `price` (decimal)
- `display_order` (int) - For menu ordering
- `active` (boolean) - Soft delete flag
- `created_at` (timestamptz)

### 3. sale_sessions
- `id` (uuid, primary key)
- `started_at` (timestamptz) - Session start time (SGT)
- `ended_at` (timestamptz, nullable) - Session end time
- `started_by` (bigint) - Telegram ID of user who started session
- `total_sales` (decimal) - Total revenue for session
- `status` (enum: 'active', 'ended')

### 4. inventory_logs
- `id` (uuid, primary key)
- `session_id` (uuid, foreign key → sale_sessions)
- `item_name` (text) - Inventory item name
- `quantity` (int) - Quantity purchased/stocked
- `cost_price` (decimal, nullable) - Optional cost tracking
- `logged_at` (timestamptz)

### 5. orders
- `id` (uuid, primary key)
- `session_id` (uuid, foreign key → sale_sessions)
- `order_number` (int) - Incremental per session
- `items` (jsonb) - Array of order items: `[{menu_item_id, name, size, price, quantity}]`
- `total_amount` (decimal) - Order total
- `payment_method` (enum: 'cash', 'paynow')
- `created_at` (timestamptz)
- `created_by` (bigint) - Telegram ID of staff who created order

## Implementation Phases

### Phase 1: Project Setup & Infrastructure
- Initialize Python virtual environment
- Install all dependencies
- Create project directory structure
- Setup .env configuration (Bot Token, Supabase URL/Key, Webhook URL)
- Create Supabase database tables with migration script
- Seed authorized_users table with Telegram IDs

### Phase 2: Core Bot & Authentication
- Setup webhook endpoint with Flask/FastAPI
- Implement authentication middleware (verify telegram_id against authorized_users)
- Create timezone utilities for Singapore Time conversion
- Setup Supabase client connection and test queries

### Phase 3: Menu Setup Flow
- First-time setup detection (no menu items exist)
- Conversation handler for adding menu items:
  - Prompt for item name and size
  - Prompt for price
  - Confirm and save to database
- Edit/delete menu items functionality
- Display current menu command

### Phase 4: Control Panel
- Main control panel inline keyboard:
  - "Start Session" button
  - "View Past Sales" button
  - "View Past Inventory" button
- View past sessions with pagination (10 per page)
- Session detail view (sales summary, orders, inventory used)

### Phase 5: Inventory Input & Session Start
- Pre-session inventory input conversation:
  - Prompt for item name
  - Prompt for quantity
  - Prompt for optional cost price
  - Add more items or finish
- Display inventory summary
- Confirm button to create new sale_session record

### Phase 6: Active Sale Session
- **Sales Dashboard**:
  - Display current total sales at top
  - Three main buttons: New Order, View Orders, End Session

- **New Order Flow**:
  - Display all menu items as inline keyboard buttons
  - Cart state management using ConversationHandler
  - Real-time cart display showing items and subtotal
  - Add/remove items with +/- buttons
  - Payment method selection: Cash or PayNow buttons
  - Confirm Order button → save to orders table

- **View Orders**:
  - Paginated list of orders (5-10 per page)
  - Each order as clickable button showing order number and total
  - Order detail view: items, quantities, total, payment method
  - Delete order button with confirmation dialog

- **End Session**:
  - Confirmation message with current date/time (SGT)
  - Display session summary:
    - Total orders
    - Total revenue
    - Items sold breakdown
    - Duration
  - Update sale_sessions.status to 'ended'
  - Return to control panel

### Phase 7: Deployment (Digital Ocean)
- Provision Digital Ocean droplet (Ubuntu)
- Install Python, dependencies
- Configure SSL certificate (Let's Encrypt)
- Setup webhook URL with HTTPS
- Configure environment variables
- Setup systemd service for bot auto-restart
- Test webhook and bot functionality

## Key Technical Decisions

### Timezone Management
- Store all timestamps as UTC in Supabase
- Convert to Singapore Time (Asia/Singapore) for display using pytz
- Use `datetime.now(pytz.timezone('Asia/Singapore'))` for current time

### Cart/Order Management
- Use `ConversationHandler` to maintain state during order creation
- Store cart in `context.user_data['cart']`
- Format: `{menu_item_id: {name, size, price, quantity}}`

### Callback Data Format
- Pattern: `action:param1:param2`
- Examples:
  - `add_item:uuid:1` - Add 1 of item with uuid
  - `view_order:session_id:order_number` - View specific order
  - `confirm_delete:order_id` - Confirm order deletion

### Pagination
- 5-10 items per page
- Callback buttons: `prev_page:page_num` and `next_page:page_num`
- Store total pages in callback data or calculate on-the-fly

### Order Numbers
- Auto-increment per session for easy reference
- Format: Session 1 → Order #1, #2, #3...
- Query: `SELECT COALESCE(MAX(order_number), 0) + 1 FROM orders WHERE session_id = ?`

### Webhook vs Polling
- Use webhook mode to reduce latency and server load
- Requires HTTPS endpoint
- Flask/FastAPI server handles incoming updates
- Set webhook URL: `https://your-domain.com/webhook/{BOT_TOKEN}`

## Environment Variables (.env)
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
WEBHOOK_URL=https://your-domain.com/webhook
PORT=8443
ENVIRONMENT=production
```

## Getting Telegram User IDs
To authorize staff members, you need their Telegram IDs:

**Method 1**: Use `@userinfobot`
- Have staff send a message to `@userinfobot`
- Bot will reply with their Telegram ID

**Method 2**: Temporary logging in your bot
```python
# Add to message handler temporarily
print(f"User ID: {update.effective_user.id}")
print(f"Username: @{update.effective_user.username}")
```

**Method 3**: Use `/start` command
- Modify bot to log all /start attempts
- Have staff run /start and capture their IDs from logs

## User Flow Diagrams

### First Time Setup
```
/start → Unauthorized Check → Welcome Message → "Let's setup your menu!"
→ Add Menu Items (loop) → Menu Complete → Control Panel
```

### Starting a Sale Session
```
Control Panel → "Start Session" → Inventory Input (loop)
→ Confirm Inventory → Create Session → Sales Dashboard
```

### Creating an Order
```
Sales Dashboard → "New Order" → Display Menu + Empty Cart
→ Click Items (add to cart) → Cart Updates
→ Select Payment Method (Cash/PayNow) → "Confirm Order"
→ Save Order → Return to Sales Dashboard (updated total)
```

### Ending a Session
```
Sales Dashboard → "End Session" → Confirmation Dialog (with timestamp)
→ Display Summary (orders count, total sales, items sold)
→ Update Session Status → Return to Control Panel
```

## Future Enhancements (Not in MVP)
- Customer-facing ordering system
- Multiple merchant support
- Sales analytics and forecasting
- Export reports (PDF/CSV)
- Item categories/grouping
- Discounts and promotions
- Table/order tracking
- Receipt printing integration

## Development Notes
- All database queries should use parameterized statements (Supabase handles this)
- Error handling for network issues (Telegram API, Supabase connection)
- Graceful degradation if Supabase is temporarily unavailable
- Log all transactions for debugging
- Use conversation timeouts to prevent stuck states
- Implement /cancel command to exit any flow

## Testing Checklist
- [ ] Authentication works (authorized users only)
- [ ] Menu CRUD operations
- [ ] Inventory input saves correctly
- [ ] Session start creates database record
- [ ] Cart state persists during order creation
- [ ] Order confirmation saves to database
- [ ] Payment method recorded correctly
- [ ] View orders pagination works
- [ ] Delete order removes from database and updates session total
- [ ] End session calculates correct totals
- [ ] All timestamps display in Singapore Time
- [ ] Webhook receives updates reliably
- [ ] Bot handles concurrent users

## Deployment Checklist
- [ ] Digital Ocean droplet provisioned
- [ ] Domain name configured (for HTTPS)
- [ ] SSL certificate installed
- [ ] Environment variables configured
- [ ] Supabase tables created
- [ ] Authorized users seeded
- [ ] Webhook URL set with Telegram
- [ ] Systemd service created
- [ ] Bot auto-restarts on failure
- [ ] Logs configured (journalctl or file-based)
- [ ] Firewall configured (allow HTTPS, SSH only)

---

**Project Status**: Planning Phase Complete
**Next Step**: Begin Phase 1 implementation
**Last Updated**: 2025-10-18
