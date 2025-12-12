# Deployment Guide for Render

This guide will help you deploy your Quantify trading journal to Render.

## Prerequisites

1. A Render account (free tier works)
2. Your code pushed to GitHub (or GitLab/Bitbucket)

## Step 1: Create PostgreSQL Database

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" → "PostgreSQL"
3. Name it `quantify-db`
4. Select "Free" plan
5. Click "Create Database"
6. **Copy the "Internal Database URL"** - you'll need this

## Step 2: Deploy Web Service

### Option A: Using render.yaml (Recommended)

1. Push your code to GitHub
2. In Render Dashboard, click "New +" → "Web Service"
3. Connect your GitHub repository
4. Render will detect `render.yaml` and use it automatically
5. The database will be created automatically and connected

### Option B: Manual Setup

1. In Render Dashboard, click "New +" → "Web Service"
2. Connect your GitHub repository
3. Configure:
   - **Name**: `quantify-trading-journal`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
4. Add Environment Variable:
   - **Key**: `DATABASE_URL`
   - **Value**: Paste the Internal Database URL from Step 1
5. Add Environment Variable:
   - **Key**: `RENDER`
   - **Value**: `true`
6. Click "Create Web Service"

## Step 3: Wait for Deployment

- First deployment takes 5-10 minutes
- Render will install dependencies and start your app
- Check the logs for any errors

## Step 4: Access Your App

- Render provides a URL like: `https://quantify-trading-journal.onrender.com`
- You can add a custom domain in Render settings

## Troubleshooting

### Database Connection Errors

- Make sure `DATABASE_URL` environment variable is set correctly
- Check that the database is in the same region as your web service
- Verify the database is running (not paused)

### App Won't Start

- Check the logs in Render dashboard
- Make sure all dependencies are in `requirements.txt`
- Verify `Procfile` exists and is correct

### Data Not Persisting

- Ensure you're using the database (not JSON files)
- Check that database migrations ran successfully
- Verify database connection in logs

## Environment Variables

Required:
- `DATABASE_URL` - Provided automatically by Render when database is linked
- `RENDER` - Set to `true` (enables production mode)

Optional:
- `PORT` - Automatically set by Render (don't override)

## Notes

- Free tier services spin down after 15 minutes of inactivity
- First request after spin-down takes ~30 seconds (cold start)
- Database on free tier has 1GB storage limit
- For production use, consider upgrading to paid plans

