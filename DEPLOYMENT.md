# Kori POS Bot - Digital Ocean App Platform Deployment Guide

This guide will walk you through deploying your Kori POS Bot to Digital Ocean's App Platform using webhooks.

## Prerequisites

- Digital Ocean account
- GitHub account with your code pushed
- Supabase database already set up
- Telegram Bot Token from @BotFather
- Your Telegram ID added to Supabase `authorized_users` table

## Step 1: Prepare Your GitHub Repository

1. **Push your code to GitHub:**

```bash
# If you haven't initialized git yet
git init
git add .
git commit -m "Initial commit - Kori POS Bot"

# Create a new repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/kori-pos-bot.git
git branch -M main
git push -u origin main
```

2. **Verify these files exist in your repo:**
   - `.do/app.yaml` - App Platform configuration
   - `requirements.txt` - Python dependencies
   - `src/main.py` - Main application file
   - All handler files in `src/bot/handlers/`

## Step 2: Create App on Digital Ocean App Platform

1. **Log in to Digital Ocean** (https://cloud.digitalocean.com)

2. **Navigate to App Platform:**
   - Click "Create" → "Apps" in the top menu
   - Or go directly to: https://cloud.digitalocean.com/apps

3. **Connect Your GitHub Repository:**
   - Select "GitHub" as the source
   - Authorize Digital Ocean to access your GitHub account
   - Select your repository: `YOUR_USERNAME/kori-pos-bot`
   - Select branch: `main`
   - Check "Autodeploy" to deploy automatically on git push

4. **Configure the App:**
   - App Platform should auto-detect the `.do/app.yaml` file
   - If not, you'll need to manually configure:
     - **Resource Type:** Web Service
     - **Build Command:** `pip install -r requirements.txt`
     - **Run Command:** `gunicorn --bind 0.0.0.0:8080 --workers 1 --threads 2 --timeout 60 src.main:app`
     - **HTTP Port:** 8080

## Step 3: Configure Environment Variables

In the App Platform console, add these environment variables:

### Required Variables:

1. **TELEGRAM_BOT_TOKEN** (Secret)
   - Value: Your bot token from @BotFather
   - Mark as "Secret" (encrypted)

2. **SUPABASE_URL** (Secret)
   - Value: `https://YOUR_PROJECT.supabase.co`
   - Mark as "Secret"

3. **SUPABASE_KEY** (Secret)
   - Value: Your Supabase anon/public key
   - Mark as "Secret"

4. **WEBHOOK_URL**
   - Value: `${APP_URL}` (this is a built-in variable)
   - **Important:** This will be auto-populated with your app's URL

5. **ENVIRONMENT**
   - Value: `production`

6. **PORT**
   - Value: `8080`

### How to Add Environment Variables:

1. In your app settings, go to "Settings" → "App-Level Environment Variables"
2. Click "Edit"
3. For each variable:
   - Click "Add Variable"
   - Enter the key (e.g., `TELEGRAM_BOT_TOKEN`)
   - Enter the value
   - For secrets, check "Encrypt"
   - Click "Save"

## Step 4: Configure App Settings

### App Info:
- **Name:** kori-pos-bot
- **Region:** Singapore (sgp) - or closest to your users

### Resource Size:
- **Plan:** Basic (starts at $5/month)
- **Size:** Basic XXS (512MB RAM, sufficient for a Telegram bot)
  - You can scale up later if needed

### HTTP Settings:
- **HTTP Port:** 8080
- **HTTP Routes:** `/` (root path)
- **Health Checks:** Enabled
  - Path: `/`
  - Initial delay: 10 seconds
  - Period: 10 seconds

## Step 5: Deploy the App

1. **Review your configuration** - Make sure all environment variables are set
2. **Click "Create Resources"** or "Deploy"
3. **Wait for deployment** (usually 2-5 minutes)
   - You can monitor progress in the "Runtime Logs" tab

## Step 6: Verify Deployment

### Check App URL:

1. Once deployed, you'll see your app URL (e.g., `https://kori-pos-bot-xxxxx.ondigitalocean.app`)
2. Visit this URL in your browser - you should see: **"Kori POS Bot is running!"**

### Check Bot Webhook:

Your webhook URL will be: `https://your-app-url.ondigitalocean.app/YOUR_BOT_TOKEN`

To verify the webhook is set correctly, run this in your terminal:

```bash
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo
```

You should see:
```json
{
  "ok": true,
  "result": {
    "url": "https://your-app-url.ondigitalocean.app/YOUR_BOT_TOKEN",
    "has_custom_certificate": false,
    "pending_update_count": 0
  }
}
```

### Test the Bot:

1. Open Telegram
2. Search for your bot
3. Send `/start`
4. You should receive the welcome message: "👋 Welcome to Kori POS, {your_name}!"

## Step 7: Monitor and Debug

### View Logs:

1. In App Platform dashboard, go to your app
2. Click "Runtime Logs" tab
3. You'll see all application logs in real-time

### Check for Errors:

Look for these log messages:
- ✅ `Initializing bot application...`
- ✅ `All handlers registered successfully`
- ✅ `Bot application initialized successfully`
- ✅ `Webhook set to: https://...`

### Common Issues:

#### Bot not responding:
- Check environment variables are set correctly
- Verify webhook is set: `curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo`
- Check runtime logs for errors

#### "Unauthorized" errors:
- Verify your Telegram ID is in the Supabase `authorized_users` table
- Check SUPABASE_URL and SUPABASE_KEY are correct

#### Webhook errors:
- Ensure WEBHOOK_URL is set to `${APP_URL}`
- Verify the app is running (health check passing)
- Check that TELEGRAM_BOT_TOKEN is correct

## Step 8: Set Up Custom Domain (Optional)

If you want a custom domain instead of `.ondigitalocean.app`:

1. Go to "Settings" → "Domains"
2. Click "Add Domain"
3. Enter your domain (e.g., `bot.yourdomain.com`)
4. Add the provided CNAME record to your DNS settings
5. Wait for DNS propagation (can take up to 24 hours)
6. SSL certificate will be automatically provisioned

**Important:** After adding a custom domain, you need to:
- Update the `WEBHOOK_URL` env variable to your custom domain
- Redeploy the app

## Step 9: Enable Auto-Deploy

Auto-deploy is already enabled if you checked the option during setup. This means:

- Every push to `main` branch triggers a new deployment
- Useful for quick updates and fixes
- You can disable this in Settings → Source if needed

## Cost Estimation

Digital Ocean App Platform pricing:

- **Basic Plan (512MB RAM):** $5/month
- **Bandwidth:** 100GB included, then $0.01/GB
- **Build minutes:** Unlimited for Basic plan

For a typical Telegram bot with moderate usage, expect around **$5-10/month**.

## Updating Your Bot

### To update code:

```bash
# Make your changes
git add .
git commit -m "Updated feature X"
git push origin main
```

App Platform will automatically detect the push and redeploy (if auto-deploy is enabled).

### To update environment variables:

1. Go to Settings → Environment Variables
2. Edit the variable
3. Click "Save"
4. Click "Deploy" to restart with new variables

## Rollback a Deployment

If something goes wrong:

1. Go to "Deployments" tab
2. Find a previous successful deployment
3. Click the "..." menu
4. Select "Redeploy"

## Scaling Your App

As your usage grows:

1. **Vertical Scaling:** Increase instance size
   - Go to Settings → Resources
   - Change from Basic XXS to Basic XS/S
   - Costs more but handles more load

2. **Horizontal Scaling:** Add more instances
   - Go to Settings → Resources
   - Increase instance count
   - **Note:** For Telegram bots, usually not needed (webhooks are stateless)

## Security Best Practices

1. ✅ Always use "Secret" encryption for sensitive variables
2. ✅ Never commit `.env` files to Git
3. ✅ Regularly rotate your Supabase keys
4. ✅ Monitor logs for unauthorized access attempts
5. ✅ Keep your Telegram Bot Token private
6. ✅ Only add authorized users to the database

## Backup Strategy

1. **Code:** Stored in GitHub (version controlled)
2. **Database:** Supabase has automatic backups
   - Daily backups for paid plans
   - Point-in-time recovery available
3. **Environment Variables:** Document them securely (password manager)

## Troubleshooting Commands

### Check webhook status:
```bash
curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo
```

### Delete webhook (if needed):
```bash
curl https://api.telegram.org/bot<TOKEN>/deleteWebhook
```

### Set webhook manually:
```bash
curl -X POST https://api.telegram.org/bot<TOKEN>/setWebhook \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-app-url.ondigitalocean.app/YOUR_TOKEN"}'
```

### Test Supabase connection:
```python
# Run this locally to test
python test_auth.py
```

## Support and Resources

- **Digital Ocean Docs:** https://docs.digitalocean.com/products/app-platform/
- **Telegram Bot API:** https://core.telegram.org/bots/api
- **python-telegram-bot Docs:** https://docs.python-telegram-bot.org/
- **Supabase Docs:** https://supabase.com/docs

## Maintenance Checklist

### Weekly:
- [ ] Check runtime logs for errors
- [ ] Monitor response times
- [ ] Verify bot is responding

### Monthly:
- [ ] Review costs and usage
- [ ] Update dependencies if needed
- [ ] Check for security updates

### Quarterly:
- [ ] Review and audit authorized users
- [ ] Backup environment variables
- [ ] Test disaster recovery

---

**Deployment Status:** Ready for production
**Last Updated:** 2025-10-18
**Version:** 1.0.0

Need help? Check the logs first, then review common issues above. Good luck! 🚀
