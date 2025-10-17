# Local Testing Guide

This guide will help you test the Kaori POS Bot on your local machine using **polling mode**.

## Prerequisites

1. **Python 3.10+** installed
2. **Supabase account** (free tier is fine)
3. **Telegram account**
4. **Telegram Bot Token** from @BotFather

## Step-by-Step Setup

### 1. Install Python Dependencies

Open terminal in the project directory:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Setup Supabase Database

#### 2.1 Create Supabase Project

1. Go to https://supabase.com
2. Sign up or log in
3. Click "New Project"
4. Fill in:
   - Project Name: `kaori-pos-bot` (or any name)
   - Database Password: Create a strong password
   - Region: Choose closest to you
5. Wait for project to initialize (~2 minutes)

#### 2.2 Run Database Schema

1. In your Supabase dashboard, click on "SQL Editor" in the left sidebar
2. Click "New Query"
3. Open the file `migrations/supabase_schema.sql` in a text editor
4. Copy ALL the contents
5. Paste into the Supabase SQL Editor
6. Click "Run" button
7. You should see: "Success. No rows returned"

#### 2.3 Get Supabase Credentials

1. In Supabase dashboard, click "Settings" (gear icon) → "API"
2. Copy these values:
   - **Project URL** (e.g., `https://xxxxx.supabase.co`)
   - **anon/public key** (the long string under "Project API keys")

#### 2.4 Add Your Telegram ID as Authorized User

First, get your Telegram ID:
1. Open Telegram
2. Search for `@userinfobot`
3. Send it any message
4. It will reply with your user ID (a number like `123456789`)

Then add it to the database:
1. In Supabase, go to "Table Editor" → "authorized_users"
2. Click "Insert" → "Insert row"
3. Fill in:
   - `telegram_id`: Your Telegram ID (the number from @userinfobot)
   - `username`: Your Telegram username (optional)
   - `full_name`: Your name (optional)
4. Click "Save"

### 3. Create Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow the prompts:
   - Bot name: `Kaori POS Bot` (or any name)
   - Username: `kaori_pos_bot` (must end with 'bot')
4. BotFather will give you a **bot token** like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`
5. **COPY THIS TOKEN** - you'll need it next

### 4. Configure Environment Variables

1. Copy the example environment file:
   ```bash
   # Windows
   copy .env.example .env

   # macOS/Linux
   cp .env.example .env
   ```

2. Edit `.env` file and fill in:
   ```env
   # Telegram Bot Configuration
   TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

   # Supabase Configuration
   SUPABASE_URL=https://xxxxx.supabase.co
   SUPABASE_KEY=your_long_anon_key_here

   # Webhook Configuration (leave empty for local development)
   WEBHOOK_URL=

   # Environment (MUST be 'development' for local testing)
   ENVIRONMENT=development
   ```

**Important:**
- Replace the bot token with YOUR actual token from BotFather
- Replace Supabase URL and key with YOUR project credentials
- Keep `ENVIRONMENT=development` for local testing
- Leave `WEBHOOK_URL` empty (or don't include it)

### 5. Run the Bot

Make sure your virtual environment is activated, then:

```bash
python src/main.py
```

You should see output like:
```
INFO - Running in DEVELOPMENT mode with polling
INFO - Bot is now running. Press Ctrl+C to stop.
```

This means the bot is running in **polling mode** (perfect for local testing).

### 6. Test the Bot

1. Open Telegram
2. Search for your bot (the username you created with BotFather)
3. Click "Start" or send `/start`
4. You should see the welcome message and control panel buttons

If you see "⛔ You are not authorized", check that:
- You added your Telegram ID to the `authorized_users` table
- The Telegram ID matches exactly (check @userinfobot again)

### 7. Test the Features

#### Test Menu Setup
1. Click "Manage Menu"
2. Click "Add New Item"
3. Enter item name (e.g., "Hojicha")
4. Enter size (e.g., "Reg")
5. Enter price (e.g., "4.50")
6. Verify the item was added

#### Test Sale Session
1. From control panel, click "Start Session"
2. Add inventory items or send `/skip`
3. Create some orders using the "New Order" button
4. Click items to add to cart
5. Confirm and select payment method
6. View orders to see your created orders
7. End the session

## Troubleshooting

### Bot not responding

**Check 1: Is the bot running?**
- You should see logs in the terminal
- If not, run `python src/main.py` again

**Check 2: Correct bot token?**
- Verify the token in `.env` matches BotFather's token
- No extra spaces or quotes

**Check 3: Virtual environment activated?**
```bash
# You should see (venv) at the start of your prompt
# If not:
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
```

### "Not authorized" error

**Check 1: Telegram ID correct?**
- Get your ID from @userinfobot
- Check it matches the `authorized_users` table in Supabase

**Check 2: Database connected?**
- Check Supabase credentials in `.env`
- Test connection by viewing `authorized_users` table in Supabase

### Import errors

**Check 1: Dependencies installed?**
```bash
pip install -r requirements.txt
```

**Check 2: Running from project root?**
```bash
# Make sure you're in kaori-pos-bot directory
cd kaori-pos-bot
python src/main.py
```

### Database errors

**Check 1: Schema created?**
- Go to Supabase → SQL Editor
- Run the entire `migrations/supabase_schema.sql` file

**Check 2: Tables exist?**
- Go to Supabase → Table Editor
- You should see 5 tables: authorized_users, menu_items, sale_sessions, inventory_logs, orders

## Environment Variables Reference

For **local testing**, your `.env` should look like:

```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
SUPABASE_URL=https://abcdefgh.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
WEBHOOK_URL=
ENVIRONMENT=development
```

**What each variable does:**
- `TELEGRAM_BOT_TOKEN` - Your bot's authentication token (from BotFather)
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase anon/public API key
- `WEBHOOK_URL` - Leave empty for local (only needed for production)
- `ENVIRONMENT` - Set to `development` for polling mode

## Switching to Production (Webhook)

When you're ready to deploy:

1. Change `.env`:
   ```env
   WEBHOOK_URL=https://your-domain.com
   ENVIRONMENT=production
   ```

2. The bot will automatically use webhook mode

## Digital Ocean App Platform

Yes! You can deploy to Digital Ocean App Platform instead of a Droplet. It's actually simpler:

### Advantages of App Platform:
- ✅ Automatic HTTPS/SSL
- ✅ No server management
- ✅ Built-in monitoring
- ✅ Auto-scaling

### Steps:
1. Push your code to GitHub
2. Create App Platform app
3. Link GitHub repository
4. Set environment variables in App Platform dashboard
5. Deploy!

I can create a detailed guide for App Platform deployment if you'd like.

## Next Steps

Once local testing is successful:
1. Test all features thoroughly
2. Add more menu items
3. Try multiple sale sessions
4. Test order deletion
5. Verify Singapore timezone is correct

When everything works locally, you're ready for production deployment!
