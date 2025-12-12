# Quick Deploy Guide - 5 Simple Steps

## Step 1: Push Your Code to GitHub

1. Open Terminal in your project folder (`/Users/jayden/Desktop/d`)
2. Run these commands:

```bash
# Initialize git if you haven't already
git init

# Add all files
git add .

# Commit
git commit -m "Ready for deployment"

# Create a new repository on GitHub.com, then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

**Don't have a GitHub account?** 
- Go to https://github.com and create a free account
- Click "New repository"
- Name it (e.g., "quantify-trading-journal")
- Don't initialize with README
- Copy the repository URL

---

## Step 2: Create Render Account

1. Go to https://render.com
2. Click "Get Started for Free"
3. Sign up with GitHub (easiest - connects automatically)
4. Or sign up with email

---

## Step 3: Create PostgreSQL Database

1. In Render dashboard, click **"New +"** button (top right)
2. Click **"PostgreSQL"**
3. Fill in:
   - **Name**: `quantify-db`
   - **Database**: `quantify` (or leave default)
   - **User**: `quantify_user` (or leave default)
   - **Region**: Choose closest to you
   - **Plan**: **Free**
4. Click **"Create Database"**
5. **Wait 2-3 minutes** for it to be ready
6. **Don't copy any URLs yet** - Render will connect automatically

---

## Step 4: Deploy Web Service

1. In Render dashboard, click **"New +"** button
2. Click **"Web Service"**
3. Click **"Connect GitHub"** (or GitLab/Bitbucket if you used that)
4. Authorize Render to access your repositories
5. Find and select your repository (`quantify-trading-journal` or whatever you named it)
6. Click **"Connect"**

7. Render will auto-detect settings (because of `render.yaml`):
   - **Name**: `quantify-trading-journal` (or change if you want)
   - **Environment**: Python 3 (auto-detected)
   - **Build Command**: `pip install -r requirements.txt` (auto-detected)
   - **Start Command**: `python app.py` (auto-detected)

8. **Important - Add Environment Variable:**
   - Scroll down to "Environment Variables"
   - Click **"Add Environment Variable"**
   - **Key**: `RENDER`
   - **Value**: `true`
   - Click **"Add"**

9. **Link Database:**
   - Scroll to "Database" section
   - Click dropdown and select `quantify-db` (the database you created)
   - This automatically sets `DATABASE_URL` for you!

10. Click **"Create Web Service"**

---

## Step 5: Wait and Test

1. **Wait 5-10 minutes** for first deployment
2. Watch the logs - you'll see:
   - Installing dependencies
   - Building...
   - Starting...
3. When you see "Your service is live", click the URL (e.g., `https://quantify-trading-journal.onrender.com`)
4. **Test it:**
   - Create an account
   - Sign in
   - Add a test trade
   - Everything should work!

---

## ✅ Done!

Your app is now live and accessible 24/7!

**Your URL will be something like:**
`https://quantify-trading-journal.onrender.com`

**To add a custom domain later:**
- Go to your service settings in Render
- Click "Custom Domains"
- Add your domain

---

## Troubleshooting

**"Build failed"**
- Check the logs - usually a missing dependency
- Make sure `requirements.txt` has all packages

**"Database connection error"**
- Make sure you linked the database in Step 4
- Check that database is running (not paused)

**"Service won't start"**
- Check logs for error messages
- Make sure `Procfile` exists in your repo

**Need help?** Check the full guide in `DEPLOYMENT.md`

