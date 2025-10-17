# Digital Ocean App Platform Deployment - Quick Checklist

## Pre-Deployment Checklist

- [ ] Code pushed to GitHub (main branch)
- [ ] Supabase database created and tables set up
- [ ] Telegram Bot created (have Bot Token from @BotFather)
- [ ] Your Telegram ID added to Supabase `authorized_users` table
- [ ] `.do/app.yaml` file exists in repository
- [ ] `requirements.txt` is up to date

## Deployment Steps

### 1. Create App on Digital Ocean
- [ ] Go to https://cloud.digitalocean.com/apps
- [ ] Click "Create" → "Apps"
- [ ] Connect GitHub repository
- [ ] Select `kori-pos-bot` repository
- [ ] Select `main` branch
- [ ] Enable "Autodeploy"

### 2. Configure Environment Variables
Add these in App Platform settings:

- [ ] **TELEGRAM_BOT_TOKEN** = `your_bot_token` (mark as Secret)
- [ ] **SUPABASE_URL** = `https://xxxxx.supabase.co` (mark as Secret)
- [ ] **SUPABASE_KEY** = `your_anon_key` (mark as Secret)
- [ ] **WEBHOOK_URL** = `${APP_URL}` (built-in variable)
- [ ] **ENVIRONMENT** = `production`
- [ ] **PORT** = `8080`

### 3. Configure App Settings
- [ ] **Region:** Singapore (sgp) or closest to you
- [ ] **Plan:** Basic
- [ ] **Size:** Basic XXS (512MB RAM)
- [ ] **HTTP Port:** 8080
- [ ] **Health Check Path:** `/`

### 4. Deploy
- [ ] Click "Create Resources"
- [ ] Wait for deployment (2-5 minutes)
- [ ] Check "Runtime Logs" for errors

### 5. Verify Deployment

#### Check App is Running:
- [ ] Visit your app URL - should show "Kori POS Bot is running!"

#### Check Webhook:
```bash
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo
```
- [ ] URL should be: `https://your-app-url.ondigitalocean.app/YOUR_BOT_TOKEN`
- [ ] `pending_update_count` should be 0

#### Test Bot:
- [ ] Open Telegram
- [ ] Send `/start` to your bot
- [ ] Should receive welcome message
- [ ] Test creating a menu item
- [ ] Test starting a session

## Post-Deployment

### Monitor for 24 Hours
- [ ] Check logs for errors every few hours
- [ ] Test all major features
- [ ] Verify database connections are stable

### Optional Improvements
- [ ] Set up custom domain
- [ ] Configure alerting for downtime
- [ ] Set up monitoring dashboard

## Environment Variables Quick Reference

```bash
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
SUPABASE_URL=https://abcdefghij.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
WEBHOOK_URL=${APP_URL}
ENVIRONMENT=production
PORT=8080
```

## Important URLs

- **App Platform Console:** https://cloud.digitalocean.com/apps
- **Telegram Bot API Docs:** https://core.telegram.org/bots/api
- **Supabase Dashboard:** https://app.supabase.com/

## Troubleshooting Quick Fixes

### Bot not responding:
```bash
# Check webhook
curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo

# Reset webhook if needed
curl https://api.telegram.org/bot<TOKEN>/deleteWebhook
```
Then redeploy the app to set webhook again.

### Database errors:
- Check Supabase URL and Key are correct
- Verify tables exist in Supabase
- Check authorized_users table has your Telegram ID

### App crashes:
- Check "Runtime Logs" in App Platform
- Verify all environment variables are set
- Ensure PORT is set to 8080

## Success Criteria

✅ App shows "Kori POS Bot is running!" at root URL
✅ Webhook is set correctly
✅ Bot responds to `/start` command
✅ No errors in runtime logs
✅ Can create menu items
✅ Can start a sale session
✅ Can create orders

---

**Estimated deployment time:** 15-30 minutes
**Estimated monthly cost:** $5-10 USD

Good luck! 🚀
