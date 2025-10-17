# Quick Start Guide

Choose your path:

## 🧪 Local Testing (Polling Mode)

**Best for:** Testing before deployment

**Environment Variables Needed:**
```env
TELEGRAM_BOT_TOKEN=your_bot_token
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your_anon_key
WEBHOOK_URL=
ENVIRONMENT=development
```

**Run:**
```bash
python src/main.py
```

**Mode:** Polling (no webhook needed)

📖 **Full Guide:** [LOCAL_TESTING.md](LOCAL_TESTING.md)

---

## 🚀 Production - Digital Ocean App Platform (Webhook Mode)

**Best for:** Easy production deployment with auto-SSL

**Environment Variables Needed:**
```env
TELEGRAM_BOT_TOKEN=your_bot_token
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your_anon_key
WEBHOOK_URL=${APP_URL}
ENVIRONMENT=production
PORT=8080
```

**Advantages:**
- ✅ No server management
- ✅ Automatic HTTPS
- ✅ Auto-deploys from GitHub
- 💰 ~$5/month

📖 **Full Guide:** [DEPLOY_APP_PLATFORM.md](DEPLOY_APP_PLATFORM.md)

---

## 🖥️ Production - Digital Ocean Droplet (Webhook Mode)

**Best for:** Full control over server

**Environment Variables Needed:**
```env
TELEGRAM_BOT_TOKEN=your_bot_token
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your_anon_key
WEBHOOK_URL=https://your-domain.com
ENVIRONMENT=production
PORT=8443
```

**Requirements:**
- Domain with SSL certificate
- Manual nginx/systemd setup
- 💰 ~$6/month + maintenance

📖 **Full Guide:** [README.md](README.md#deployment-digital-ocean)

---

## 📋 Environment Variable Reference

| Variable | Local | App Platform | Droplet |
|----------|-------|--------------|---------|
| `TELEGRAM_BOT_TOKEN` | ✅ Required | ✅ Required | ✅ Required |
| `SUPABASE_URL` | ✅ Required | ✅ Required | ✅ Required |
| `SUPABASE_KEY` | ✅ Required | ✅ Required | ✅ Required |
| `WEBHOOK_URL` | ❌ Leave empty | `${APP_URL}` | Your domain |
| `ENVIRONMENT` | `development` | `production` | `production` |
| `PORT` | Any | `8080` | `8443` |

---

## 🔑 Get Your Credentials

### Telegram Bot Token
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot`
3. Follow instructions
4. Copy the token

### Your Telegram ID
1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. Copy the user ID number

### Supabase Credentials
1. Create project at [supabase.com](https://supabase.com)
2. Go to Settings → API
3. Copy:
   - Project URL
   - anon/public key

---

## 🎯 Recommended Path

1. **Start:** Local testing with polling mode
2. **Test:** All features thoroughly
3. **Deploy:** App Platform for production (easiest)
4. **Later:** Switch to Droplet if you need more control

---

## 🆘 Need Help?

- **Local Testing Issues:** See [LOCAL_TESTING.md](LOCAL_TESTING.md#troubleshooting)
- **App Platform Issues:** See [DEPLOY_APP_PLATFORM.md](DEPLOY_APP_PLATFORM.md#troubleshooting)
- **Droplet Issues:** See [README.md](README.md#troubleshooting)
