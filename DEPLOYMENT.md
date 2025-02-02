# Deployment Guide

This guide will help you deploy Moodify while maintaining the exact same functionality as the local version.

## Step 1: Deploy Backend to Render

1. Create a Render account at [render.com](https://render.com)

2. Create a new Web Service:
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Name: `moodify-backend` (or your preferred name)
   - Select the main branch

3. Configure the service:
   - Environment: `Docker`
   - Region: Choose the closest to your users
   - Instance Type: Free (Starter)
   - Auto-Deploy: Yes

4. Add Environment Variables:
   ```
   TEMP_DIR=/app/temp
   DEBUG=False
   ```

5. Click "Create Web Service"

Note: The first build might take 5-10 minutes. Render will automatically detect your Dockerfile.

## Step 2: Deploy Frontend to Vercel

1. Create a Vercel account at [vercel.com](https://vercel.com)

2. Install Vercel CLI (optional, for testing):
   ```bash
   npm install -g vercel
   ```

3. Deploy to Vercel:
   - Go to [vercel.com/new](https://vercel.com/new)
   - Import your GitHub repository
   - Configure project:
     - Framework Preset: Other
     - Build Command: None
     - Output Directory: ./
   - Click "Deploy"

4. Update API URL:
   - Go to your deployed frontend
   - Open the browser console (F12)
   - Your frontend will be deployed to moodi-fy.vercel.app
   - The backend API is at moodi-fy.onrender.com

## Step 3: Final Configuration

1. Update CORS in your backend:
   - Go to Render dashboard
   - Add environment variable:
     ```
     ALLOWED_ORIGINS=https://moodi-fy.vercel.app
     ```

2. Redeploy the backend:
   - Go to Render dashboard
   - Click "Manual Deploy" → "Deploy latest commit"

## Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the backend:
   ```bash
   python app.py
   ```

3. Serve the frontend:
   ```bash
   npx http-server . -p 8080
   ```

## Important Notes

1. Cold Starts:
   - The free tier of Render spins down after 15 minutes of inactivity
   - First request after inactivity may take 30 seconds
   - Subsequent requests will be fast

2. File Processing:
   - Temporary files are stored in /app/temp on Render
   - Files are automatically cleaned up

3. Monitoring:
   - Check Render logs for backend issues
   - Use browser console for frontend issues

4. Scaling:
   - Free tier is perfect for testing user interest
   - Easy to upgrade to paid tier when needed
   - No code changes required to scale
