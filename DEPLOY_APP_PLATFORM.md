# Digital Ocean App Platform Deployment Guide

Deploy the Kaori POS Bot to Digital Ocean App Platform with automatic HTTPS and no server management.

## Why App Platform vs Droplet?

**App Platform (Recommended for this bot):**
- ✅ Automatic SSL/HTTPS certificates
- ✅ No server management (no SSH, updates, etc.)
- ✅ Built-in monitoring and logs
- ✅ Easy environment variable management
- ✅ Auto-restarts on crashes
- ✅ Git-based deployments
- 💰 ~$5/month for basic plan

**Droplet (Traditional VPS):**
- More control over server
- Manual SSL setup required
- You manage updates, security, etc.
- Good for complex setups
- 💰 ~$6/month + more maintenance time

## Prerequisites

1. **GitHub account** (to host your code)
2. **Digital Ocean account** (get $200 credit with referral links)
3. **Supabase project** already set up
4. **Telegram bot** already created

## Step-by-Step Deployment

### Step 1: Prepare Your Code for Production

#### 1.1 Create a `Procfile`

Create a file named `Procfile` (no extension) in the project root:

```bash
web: python src/main.py
```

This tells App Platform how to run your bot.

#### 1.2 Verify requirements.txt

Make sure `requirements.txt` includes all dependencies (already done).

#### 1.3 Create runtime.txt (optional)

Create `runtime.txt` to specify Python version:

```
python-3.11.0
```

### Step 2: Push Code to GitHub

#### 2.1 Initialize Git (if not already done)

```bash
git init
git add .
git commit -m "Initial commit - Kaori POS Bot"
```

#### 2.2 Create GitHub Repository

1. Go to https://github.com
2. Click "New repository"
3. Name it: `kaori-pos-bot`
4. Keep it **Private** (recommended)
5. Don't initialize with README (we already have one)
6. Click "Create repository"

#### 2.3 Push to GitHub

```bash
git remote add origin https://github.com/YOUR_USERNAME/kaori-pos-bot.git
git branch -M main
git push -u origin main
```

### Step 3: Create App Platform App

#### 3.1 Create New App

1. Log in to Digital Ocean: https://cloud.digitalocean.com
2. Click "Create" → "Apps"
3. Click "GitHub" as source
4. Authorize Digital Ocean to access your GitHub (if first time)
5. Select your `kaori-pos-bot` repository
6. Choose branch: `main`
7. Check "Autodeploy" (redeploy on git push)
8. Click "Next"

#### 3.2 Configure App Settings

**Resources:**
- Type: Web Service
- Name: `kaori-pos-bot`
- Region: Choose closest to you
- Branch: `main`
- Source Directory: `/` (root)

**Build & Deploy:**
- Build Command: (leave default or blank)
- Run Command: `python src/main.py`

**Plan:**
- Select "Basic" plan ($5/month)
- Or "Professional" if you need more resources

Click "Next"

#### 3.3 Set Environment Variables

In the "Environment Variables" section, add these variables:

| Key | Value | Encrypted? |
|-----|-------|-----------|
| `TELEGRAM_BOT_TOKEN` | `your_bot_token_from_botfather` | ✅ Yes |
| `SUPABASE_URL` | `https://xxxxx.supabase.co` | ❌ No |
| `SUPABASE_KEY` | `your_supabase_anon_key` | ✅ Yes |
| `WEBHOOK_URL` | `${APP_URL}` | ❌ No |
| `ENVIRONMENT` | `production` | ❌ No |
| `PORT` | `8080` | ❌ No |

**Important Notes:**
- `${APP_URL}` is a special variable that App Platform provides automatically
- Mark sensitive data (tokens, keys) as "Encrypted"
- Port must be `8080` for App Platform

Click "Next"

#### 3.4 Review and Create

1. Review all settings
2. App name: `kaori-pos-bot` (or your choice)
3. Click "Create Resources"

### Step 4: Wait for Deployment

1. App Platform will:
   - Pull your code from GitHub
   - Install Python and dependencies
   - Start your bot
   - Assign a URL (like `https://kaori-pos-bot-xxxxx.ondigitalocean.app`)

2. This takes 5-10 minutes

3. Watch the build logs in the "Build Logs" tab

### Step 5: Verify Deployment

#### 5.1 Check App Status

1. In App Platform dashboard, status should show "Active" (green)
2. Click on your app to see details

#### 5.2 Check Logs

1. Click "Runtime Logs" tab
2. You should see:
   ```
   Running in PRODUCTION mode with webhook
   Webhook set to: https://your-app-url.ondigitalocean.app/your_bot_token
   Starting webhook server on port 8080
   ```

#### 5.3 Test the Bot

1. Open Telegram
2. Find your bot
3. Send `/start`
4. You should get the control panel!

If it works, you're done! 🎉

### Step 6: Get Custom Domain (Optional)

Instead of the default `.ondigitalocean.app` URL:

1. In App Platform, go to "Settings" → "Domains"
2. Click "Add Domain"
3. Enter your domain (e.g., `bot.yourdomain.com`)
4. Follow DNS setup instructions
5. App Platform will automatically provision SSL

Then update environment variable:
- `WEBHOOK_URL` = `https://bot.yourdomain.com`

## Managing Your App

### View Logs

```
App Platform Dashboard → Your App → Runtime Logs
```

### Update Environment Variables

```
App Platform Dashboard → Your App → Settings → Environment Variables
```

After changing env vars, the app will automatically redeploy.

### Redeploy

**Manual:**
```
App Platform Dashboard → Your App → Actions → Force Rebuild and Deploy
```

**Automatic:**
Just push to GitHub:
```bash
git add .
git commit -m "Update bot"
git push
```

App Platform will automatically redeploy.

### Scale Resources

```
App Platform Dashboard → Your App → Settings → Edit Plan
```

You can upgrade to more CPU/RAM if needed.

### View Metrics

```
App Platform Dashboard → Your App → Insights
```

Shows CPU, memory, bandwidth usage.

## Cost Breakdown

**Basic Plan (~$5/month):**
- 512 MB RAM
- 1 vCPU
- Good for moderate usage (hundreds of orders/day)

**Professional Plan (~$12/month):**
- 1 GB RAM
- 1 vCPU
- Better for heavy usage

**Supabase (Free Tier):**
- 500 MB database
- 50 MB file storage
- Good for thousands of orders

**Total: ~$5-12/month** (depending on usage)

## Troubleshooting

### Bot not responding in Telegram

**Check 1: App Status**
- Go to App Platform dashboard
- Status should be "Active" (green)
- If red, check build/runtime logs

**Check 2: Runtime Logs**
- Click "Runtime Logs"
- Look for errors
- Verify webhook was set successfully

**Check 3: Environment Variables**
- Check all env vars are set correctly
- `ENVIRONMENT` must be `production`
- `WEBHOOK_URL` should be `${APP_URL}`
- Bot token should have no spaces

**Check 4: Telegram Webhook**
- Bot can only have ONE webhook
- If you ran locally recently, it might still have old webhook
- Fix: Send this in browser:
  ```
  https://api.telegram.org/bot<YOUR_BOT_TOKEN>/deleteWebhook
  ```
- Then redeploy the app

### Build failures

**Check 1: requirements.txt**
- Make sure all dependencies are listed
- Versions compatible with Python 3.11

**Check 2: Python version**
- Check `runtime.txt` specifies correct version
- Or remove `runtime.txt` to use default

**Check 3: Build Logs**
- Read error messages carefully
- Usually shows which package failed

### Database connection errors

**Check Supabase credentials:**
- `SUPABASE_URL` correct?
- `SUPABASE_KEY` correct (use anon/public key)?
- Mark `SUPABASE_KEY` as encrypted

### High CPU/Memory usage

**Upgrade plan:**
```
Settings → Edit Plan → Professional
```

Or optimize code (but current code is already efficient).

## Updating the Bot

### Method 1: Git Push (Recommended)

```bash
# Make your changes
git add .
git commit -m "Add new feature"
git push
```

App Platform auto-deploys in ~5 minutes.

### Method 2: Manual Redeploy

In App Platform dashboard:
```
Actions → Force Rebuild and Deploy
```

## Rollback to Previous Version

```
App Platform Dashboard → Your App → Deployments → [Select old deployment] → Redeploy
```

## Security Best Practices

1. **Keep repository private** on GitHub
2. **Encrypt sensitive env vars** (tokens, keys)
3. **Regularly update dependencies**:
   ```bash
   pip list --outdated
   pip install --upgrade <package>
   ```
4. **Monitor logs** for suspicious activity
5. **Backup Supabase database** regularly (Supabase has auto-backups)

## Monitoring & Alerts

### Set up Alerts

1. Go to "Settings" → "Alerts"
2. Add email notifications for:
   - App crashes
   - High CPU usage
   - Deployment failures

### Check Health

URL: `https://your-app-url.ondigitalocean.app/`

Should return: "Kaori POS Bot is running!"

## Comparison: App Platform vs Droplet for This Bot

| Feature | App Platform | Droplet |
|---------|-------------|---------|
| Setup Time | 15 minutes | 1-2 hours |
| SSL/HTTPS | Automatic | Manual (certbot) |
| Maintenance | Zero | Regular updates needed |
| Monitoring | Built-in | Setup required |
| Auto-restart | Yes | Setup systemd |
| Scaling | Click a button | Manual |
| Cost | $5/month | $6/month + time |
| **Recommendation** | ✅ **Best for this bot** | For complex needs |

## Next Steps After Deployment

1. Test all features in production
2. Monitor logs for first few days
3. Set up email alerts
4. Consider custom domain
5. Regular backups of Supabase data

## Support

- **Digital Ocean Docs**: https://docs.digitalocean.com/products/app-platform/
- **Supabase Docs**: https://supabase.com/docs
- **Telegram Bot API**: https://core.telegram.org/bots/api

---

**Congratulations!** Your bot is now live and accessible 24/7! 🎉
