# Kaori POS Bot

A Telegram-based Point of Sale (POS) system for merchants to manage sales, inventory, and orders through a user-friendly chat interface.

## Features

- **Menu Management**: Add, edit, and manage menu items with different sizes and prices
- **Inventory Tracking**: Log starting inventory for each sale session
- **Sales Sessions**: Start and end sale sessions with automatic total calculation
- **Order Management**: Create, view, and delete orders with payment method tracking
- **Real-time Dashboard**: Monitor total sales and order count during active sessions
- **Singapore Time**: All timestamps in Singapore timezone (SGT)
- **Authentication**: Telegram ID-based access control

## Tech Stack

- **Backend**: Python 3.10+
- **Bot Framework**: python-telegram-bot (webhook mode)
- **Database**: Supabase (PostgreSQL)
- **Timezone**: pytz
- **Web Server**: Flask

## Project Structure

```
kaori-pos-bot/
├── src/
│   ├── bot/
│   │   ├── handlers/
│   │   │   ├── control_panel.py    # Main control panel
│   │   │   ├── setup.py            # Menu setup
│   │   │   ├── inventory.py        # Inventory input
│   │   │   ├── sales.py            # Active sales session
│   │   │   └── orders.py           # Order management
│   │   ├── keyboards.py            # Inline keyboards
│   │   └── middleware.py           # Authentication
│   ├── database/
│   │   ├── supabase_client.py      # Supabase connection
│   │   └── models.py               # Database queries
│   ├── utils/
│   │   ├── timezone.py             # SGT utilities
│   │   └── formatters.py           # Message formatting
│   └── main.py                     # Bot entry point
├── migrations/
│   └── supabase_schema.sql         # Database schema
├── requirements.txt
├── .env.example
└── README.md
```

## Setup Instructions

### 1. Prerequisites

- Python 3.10 or higher
- Supabase account
- Telegram Bot Token (from @BotFather)
- Domain with SSL certificate (for webhook)

### 2. Clone Repository

```bash
git clone <repository-url>
cd kaori-pos-bot
```

### 3. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Setup Supabase Database

1. Create a new Supabase project at https://supabase.com
2. Go to SQL Editor in your Supabase dashboard
3. Copy and paste the contents of `migrations/supabase_schema.sql`
4. Run the SQL script to create all tables and functions
5. Add authorized users to the `authorized_users` table:

```sql
INSERT INTO authorized_users (telegram_id, username, full_name)
VALUES (YOUR_TELEGRAM_ID, 'your_username', 'Your Name');
```

**To get your Telegram ID:**
- Send a message to [@userinfobot](https://t.me/userinfobot) on Telegram
- It will reply with your user ID

### 6. Create Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Copy the bot token provided by BotFather

### 7. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and fill in your credentials:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
WEBHOOK_URL=https://your-domain.com
PORT=8443
ENVIRONMENT=production
```

### 8. Run the Bot

**Local Development (polling mode - for testing):**

For local testing, you can modify `src/main.py` to use polling instead of webhook. However, webhook is recommended for production.

**Production (webhook mode):**

```bash
python src/main.py
```

The bot will start and listen for incoming webhook requests on the specified port.

## Deployment (Digital Ocean)

### 1. Create Droplet

1. Log in to Digital Ocean
2. Create a new Ubuntu droplet (22.04 LTS)
3. Choose appropriate size (Basic plan is sufficient)
4. Add your SSH key

### 2. Connect to Server

```bash
ssh root@your_droplet_ip
```

### 3. Install Dependencies

```bash
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx git
```

### 4. Clone and Setup Project

```bash
cd /opt
git clone <repository-url> kaori-pos-bot
cd kaori-pos-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5. Configure Environment

```bash
cp .env.example .env
nano .env  # Edit with your credentials
```

### 6. Setup Nginx

Create nginx configuration:

```bash
nano /etc/nginx/sites-available/kaori-pos-bot
```

Add:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8443;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable the site:

```bash
ln -s /etc/nginx/sites-available/kaori-pos-bot /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

### 7. Setup SSL Certificate

```bash
certbot --nginx -d your-domain.com
```

### 8. Create Systemd Service

```bash
nano /etc/systemd/system/kaori-pos-bot.service
```

Add:

```ini
[Unit]
Description=Kaori POS Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/kaori-pos-bot
Environment="PATH=/opt/kaori-pos-bot/venv/bin"
ExecStart=/opt/kaori-pos-bot/venv/bin/python src/main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
systemctl daemon-reload
systemctl enable kaori-pos-bot
systemctl start kaori-pos-bot
systemctl status kaori-pos-bot
```

### 9. Check Logs

```bash
journalctl -u kaori-pos-bot -f
```

## Usage Guide

### Starting the Bot

1. Open Telegram and search for your bot
2. Send `/start` command
3. If authorized, you'll see the control panel

### Menu Management

1. Click "Manage Menu" from control panel
2. Click "Add New Item" to add menu items
3. Enter item name (e.g., "Hojicha")
4. Enter size (e.g., "Reg", "Large")
5. Enter price (e.g., "4.50")

### Starting a Sale Session

1. Click "Start Session" from control panel
2. Enter starting inventory items (optional)
3. For each inventory item:
   - Enter item name
   - Enter quantity
   - Enter cost price (optional)
4. Confirm to start the session

### Creating Orders

1. From the sales dashboard, click "New Order"
2. Click menu items to add to cart
3. Click items multiple times to increase quantity
4. Click "Confirm" when done
5. Select payment method (Cash or PayNow)
6. Order is created and total sales updated

### Viewing Orders

1. From sales dashboard, click "View Orders"
2. Click any order to view details
3. You can delete orders if needed

### Ending a Session

1. From sales dashboard, click "End Session"
2. Review the confirmation (date/time/total)
3. Click "Yes, End Session"
4. View session summary
5. Return to control panel

## Troubleshooting

### Bot not responding

1. Check if the bot is running: `systemctl status kaori-pos-bot`
2. Check logs: `journalctl -u kaori-pos-bot -f`
3. Verify webhook is set: Check Telegram API response
4. Ensure SSL certificate is valid

### Database connection errors

1. Verify Supabase credentials in `.env`
2. Check if Supabase project is active
3. Verify network connectivity to Supabase

### Authorization issues

1. Verify your Telegram ID is in the `authorized_users` table
2. Check if the bot is querying the correct Supabase project
3. Review authentication logs

## Development

### Running Locally

For local development, you may want to use polling instead of webhook:

1. Modify `src/main.py` to use `application.run_polling()`
2. Comment out webhook setup
3. Run: `python src/main.py`

### Adding New Features

1. Create handler functions in appropriate files under `src/bot/handlers/`
2. Add keyboard layouts to `src/bot/keyboards.py`
3. Register handlers in `src/main.py`
4. Add database queries to `src/database/models.py` if needed

## License

This project is private and proprietary.

## Support

For issues or questions, please contact the administrator.
