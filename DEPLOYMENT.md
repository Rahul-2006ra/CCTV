# CCTV Intelligence — Universal Deployment Guide

This guide details how to deploy the full CCTV Intelligence application (React Frontend + FastAPI Backend + YOLOv8 + CLIP AI Models + Vector DB) to obtain a **public universal HTTPS URL** for competition submission.

---

## 🏆 Top Recommended Deployment Platforms

### Option 1: Railway (Recommended — Best for Competitions)
Railway supports full Docker containers, provides generous RAM for PyTorch/CLIP, and automatically provisions a public HTTPS domain.

1. **Push your code to GitHub** (already configured on branch `main`).
2. Go to [railway.app](https://railway.app) and sign in with GitHub.
3. Click **"New Project"** → **"Deploy from GitHub repo"**.
4. Select your `Rahul-2006ra/CCTV` repository.
5. Railway detects the `Dockerfile` and `railway.toml` automatically:
   - It will build the frontend and backend together.
   - Go to **Settings** → **Networking** → Click **"Generate Domain"**.
6. You will receive a universal HTTPS URL (e.g. `https://cctv-production.up.railway.app`).
   - Open this single link in any browser: the entire frontend and backend work together seamlessly!

---

### Option 2: Hugging Face Spaces (100% Free AI Compute)
Hugging Face Spaces provides 16GB RAM for Docker apps, which is ideal for AI/ML competition judges.

1. Go to [huggingface.co/spaces](https://huggingface.co/spaces) and click **"Create new Space"**.
2. Space Name: `cctv-intelligence`.
3. License: `mit` or `apache-2.0`.
4. Select **Space SDK**: **Docker** (Blank).
5. Click **Create Space**.
6. In your local terminal, add the Hugging Face git remote and push:
   ```bash
   git remote add space https://huggingface.co/spaces/<YOUR_HF_USERNAME>/cctv-intelligence
   git push space main
   ```
7. Hugging Face will automatically build the Dockerfile and launch your app with a permanent public link:
   `https://huggingface.co/spaces/<YOUR_HF_USERNAME>/cctv-intelligence`

---

### Option 3: Instant Universal Link from Local PC (Cloudflare Tunnel)
If your competition submission is due immediately and you want judges to access your running localhost application with zero cloud setup:

1. Download the official Cloudflare Tunnel tool:
   - [Cloudflare Tunnel Releases](https://github.com/cloudflare/cloudflared/releases/latest)
   - Or install via PowerShell:
     ```powershell
     winget install Cloudflare.cloudflared
     ```
2. Start both backend and frontend, or run the unified backend:
   ```powershell
   cloudflared tunnel --url http://127.0.0.1:8000
   ```
3. Cloudflare will print a secure, public HTTPS link (e.g., `https://random-words.trycloudflare.com`).
4. Give that link to the competition judges. Anyone in the world can test the app directly!

---

### Option 4: Render
1. Go to [render.com](https://render.com) and create a **New Web Service**.
2. Connect your GitHub repository `Rahul-2006ra/CCTV`.
3. Choose **Docker** environment.
4. Render will deploy using the root `Dockerfile` and `render.yaml`.
5. In the dashboard, copy your public `.onrender.com` URL.

---

## 🛠 Local Docker Verification

To build and run the unified container locally on your own machine:

```bash
# Build the Docker image
docker build -t cctv-intelligence .

# Run the container on port 8000
docker run -p 8000:8000 cctv-intelligence
```

Then visit:
- **Web App**: `http://localhost:8000/`
- **Footage Library**: `http://localhost:8000/footage`
- **Investigation**: `http://localhost:8000/investigation`
- **API Health**: `http://localhost:8000/api/system/health`
