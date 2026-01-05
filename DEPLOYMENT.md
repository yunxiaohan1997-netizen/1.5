# 🚀 Deployment Guide - GitHub + Railway

## Overview

This guide covers deploying the Autonomous Vehicles Alliance Game to:
1. **GitHub** - Source code repository
2. **Railway** - Backend hosting (with auto-deploy from GitHub)
3. **Frontend** - Static hosting (GitHub Pages, Netlify, or Vercel)

---

## Part 1: Deploy to GitHub

### Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `autonomous-vehicles-alliance-game` (or your choice)
3. Description: `Academic-grade AI simulation for strategic management research`
4. Make it **Public** (for GitHub Pages) or **Private** (if preferred)
5. **Do NOT** initialize with README (we already have files)
6. Click "Create repository"

### Step 2: Prepare Your Files

Your project structure should look like:

```
autonomous-vehicles-alliance-game/
├── backend/
│   ├── main.py
│   ├── agents.py
│   ├── strategies.py
│   ├── payoffs.py
│   ├── models.py
│   ├── requirements.txt
│   ├── Procfile
│   ├── railway.json
│   ├── .gitignore
│   ├── .env.example
│   ├── 11_29.xlsx
│   └── README.md
├── frontend/
│   └── index.html (renamed from autonomous-vehicles-alliance-simulation.html)
├── docs/
│   ├── QUICK_START.md
│   ├── PROJECT_COMPLETE.md
│   └── FILE_INVENTORY.md
└── README.md (root README for GitHub)
```

### Step 3: Initialize Git and Push

```bash
# Navigate to your project directory
cd /path/to/your/project

# Initialize git
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: Academic-grade AI simulation system"

# Add remote (replace with your GitHub URL)
git remote add origin https://github.com/YOUR-USERNAME/autonomous-vehicles-alliance-game.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### Step 4: Verify on GitHub

Go to your repository URL and verify all files are uploaded.

---

## Part 2: Deploy Backend to Railway

### Step 1: Create Railway Account

1. Go to https://railway.app
2. Sign up with GitHub (recommended for auto-deploy)
3. Verify your email

### Step 2: Create New Project

1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Authorize Railway to access your GitHub
4. Select your `autonomous-vehicles-alliance-game` repository
5. Railway will detect it's a Python project automatically

### Step 3: Configure Root Directory

Since your backend is in the `backend/` subdirectory:

1. In Railway dashboard, go to your project
2. Click "Settings"
3. Under "Build & Deploy":
   - **Root Directory**: `backend`
   - **Build Command**: (leave default or `pip install -r requirements.txt`)
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Step 4: Add Environment Variables

1. In Railway, go to "Variables" tab
2. Add the following variables:

```
OPENAI_API_KEY=sk-proj-your-actual-key-here
LOG_LEVEL=INFO
```

**IMPORTANT**: Get your OpenAI API key from https://platform.openai.com/api-keys

### Step 5: Deploy

1. Railway will automatically deploy
2. Wait 2-3 minutes for build to complete
3. You'll see logs in the "Deployments" tab
4. Once deployed, click "Generate Domain" to get your public URL
5. Your API will be at: `https://your-app-name.up.railway.app`

### Step 6: Test Your Backend

```bash
# Test the health endpoint
curl https://your-app-name.up.railway.app/

# Should return:
# {"status":"online","service":"Autonomous Vehicles Alliance Game API","version":"1.0.0"}
```

---

## Part 3: Deploy Frontend

You have three options for hosting the frontend:

### Option A: GitHub Pages (Recommended - Free)

1. **Prepare frontend**:
   ```bash
   cd frontend
   # Rename file for GitHub Pages
   mv autonomous-vehicles-alliance-simulation.html index.html
   ```

2. **Update API URL in index.html**:
   ```javascript
   // Find this line (around line 10-20):
   const API_BASE = "http://localhost:8000";
   
   // Change to your Railway URL:
   const API_BASE = "https://your-app-name.up.railway.app";
   ```

3. **Enable GitHub Pages**:
   - Go to your GitHub repository
   - Settings → Pages
   - Source: Deploy from a branch
   - Branch: `main` → `/frontend` folder
   - Save

4. **Access your site**:
   - URL will be: `https://YOUR-USERNAME.github.io/autonomous-vehicles-alliance-game/`
   - Wait 1-2 minutes for deployment

### Option B: Netlify (Easy, Free)

1. Go to https://netlify.com
2. Sign up / Sign in
3. "Add new site" → "Import an existing project"
4. Connect to GitHub
5. Select your repository
6. Build settings:
   - Base directory: `frontend`
   - Build command: (leave empty)
   - Publish directory: `.` (current directory)
7. Add environment variable (if using Netlify functions):
   - `API_BASE=https://your-app-name.up.railway.app`
8. Deploy!

### Option C: Vercel (Fast, Free)

1. Go to https://vercel.com
2. Sign up with GitHub
3. "Import Project"
4. Select your repository
5. Configure:
   - Framework Preset: Other
   - Root Directory: `frontend`
   - Build Command: (leave empty)
6. Deploy!

Then update `index.html` with your Railway URL.

---

## Part 4: Connect Frontend to Backend

### Update CORS in Backend

Your Railway backend already has CORS enabled for all origins:
```python
allow_origins=["*"]  # In main.py
```

For production, you might want to restrict this:
```python
allow_origins=[
    "https://YOUR-USERNAME.github.io",
    "https://your-netlify-site.netlify.app",
    "http://localhost:3000"  # for local development
]
```

### Update Frontend API URL

In your `index.html` (or `autonomous-vehicles-alliance-simulation.html`), find:

```javascript
const API_BASE = "http://localhost:8000";
```

Change to:
```javascript
const API_BASE = "https://your-app-name.up.railway.app";
```

Commit and push:
```bash
git add frontend/index.html
git commit -m "Update API URL to Railway backend"
git push
```

---

## Part 5: Verify Everything Works

### Test Backend

```bash
# Health check
curl https://your-app-name.up.railway.app/

# Start simulation
curl -X POST https://your-app-name.up.railway.app/api/simulation/start \
  -H "Content-Type: application/json" \
  -d '{
    "num_rounds": 3,
    "information_mode": "asymmetric",
    "am_strategy": "cooperative",
    "mc_strategy": "competitive"
  }'
```

### Test Frontend

1. Go to your frontend URL
2. Click "Start Simulation"
3. Watch AI agents make decisions
4. Test chat feature
5. Export data

---

## Troubleshooting

### Backend Issues

**"Application failed to respond"**
- Check Railway logs for errors
- Verify OPENAI_API_KEY is set
- Check that 11_29.xlsx is included in repo

**"OpenAI API error"**
- Verify your API key is correct
- Check you have GPT-4 access
- Ensure you have credits on OpenAI account

**"Payoff matrix not found"**
- Ensure 11_29.xlsx is in backend/ directory
- Check it's committed to git
- Verify file size is reasonable (< 1MB)

### Frontend Issues

**"Network Error" or CORS**
- Verify API_BASE URL is correct (with https://)
- Check Railway backend is deployed and running
- Open browser console (F12) to see exact error

**Frontend not updating**
- GitHub Pages: Wait 2-3 minutes
- Netlify: Should be instant
- Vercel: Should be instant
- Try hard refresh (Ctrl+Shift+R)

### Railway Issues

**Build failing**
- Check requirements.txt has all dependencies
- Verify Python version compatibility
- Review build logs in Railway dashboard

**Out of credits**
- Railway free tier: 500 hours/month
- Should be enough for development
- Upgrade if needed: $5/month

---

## Cost Breakdown

### Railway Hosting
- **Free Tier**: 500 hours/month (~$0)
- **Hobby Plan**: $5/month (if needed)
- Includes auto-deploy, custom domain, SSL

### OpenAI API
- **Per simulation**: $0.30-0.60 (10 rounds)
- **100 simulations**: ~$30-60
- **1000 simulations**: ~$300-600

### Frontend Hosting
- **GitHub Pages**: Free
- **Netlify**: Free
- **Vercel**: Free

**Total Monthly Cost**: $0-5 for hosting + OpenAI usage

---

## Production Considerations

### Security

1. **Environment Variables**:
   - Never commit `.env` file
   - Use Railway's variable management
   - Rotate API keys regularly

2. **CORS**:
   - Restrict to specific domains in production
   - Update `allow_origins` in main.py

3. **Rate Limiting**:
   - Consider adding rate limits to API
   - Monitor OpenAI usage
   - Set budget alerts on OpenAI

### Monitoring

1. **Railway Logs**:
   - Monitor for errors
   - Track request patterns
   - Set up alerts

2. **OpenAI Dashboard**:
   - Track token usage
   - Monitor costs
   - Set budget limits

### Scaling

**If you need more performance**:

1. **Railway**: Upgrade to Pro plan ($20/month)
   - More memory
   - Faster CPU
   - No sleep

2. **Backend**: 
   - Add Redis for state persistence
   - Use PostgreSQL for data storage
   - Implement request queue

3. **Frontend**:
   - Use CDN
   - Optimize assets
   - Enable caching

---

## Maintenance

### Updates

```bash
# Make changes locally
# Test locally
python backend/test_backend.py

# Commit and push
git add .
git commit -m "Description of changes"
git push

# Railway auto-deploys from main branch
# Frontend auto-updates (GitHub Pages/Netlify/Vercel)
```

### Monitoring Usage

**Railway Dashboard**:
- Check deployment status
- View logs
- Monitor resource usage

**OpenAI Dashboard**:
- Track API usage
- Review costs
- Manage keys

---

## Quick Command Reference

### Git Commands
```bash
git add .
git commit -m "message"
git push
git pull
git status
```

### Railway CLI (optional)
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to project
railway link

# Check logs
railway logs

# Deploy
railway up
```

### Test API Endpoints
```bash
# Health check
curl https://your-app.railway.app/

# Start simulation
curl -X POST https://your-app.railway.app/api/simulation/start \
  -H "Content-Type: application/json" \
  -d '{"num_rounds": 3, "information_mode": "asymmetric", "am_strategy": "cooperative", "mc_strategy": "competitive"}'

# List simulations
curl https://your-app.railway.app/api/simulations
```

---

## Support

If you encounter issues:

1. Check Railway logs for backend errors
2. Check browser console (F12) for frontend errors
3. Verify environment variables are set
4. Test API endpoints with curl
5. Review CORS settings

---

## Success Checklist

- [ ] GitHub repository created and files pushed
- [ ] Railway project created and deployed
- [ ] OPENAI_API_KEY environment variable set
- [ ] Backend health check passes
- [ ] Frontend deployed (GitHub Pages/Netlify/Vercel)
- [ ] Frontend API_BASE URL updated
- [ ] Test simulation runs successfully
- [ ] Chat feature works
- [ ] Data export works
- [ ] Custom domain configured (optional)

---

**Congratulations! Your academic AI simulation is now live!** 🎉

Students and researchers worldwide can now access your system.

**Share your URL**:
- Backend API: `https://your-app.railway.app`
- Frontend: `https://YOUR-USERNAME.github.io/autonomous-vehicles-alliance-game/`
