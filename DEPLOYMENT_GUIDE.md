# 🚀 Free Cloud Deployment Guide

This guide explains how to deploy the **AI Classroom Attendance Web Studio** to top free cloud platforms with **live webcam support (HTTPS)**.

---

## 🏆 Recommended Free Platforms Comparison

| Platform | Free Tier | Credit Card Needed? | Setup Time | Webcam Support (HTTPS) |
| :--- | :--- | :--- | :--- | :--- |
| **Render** *(Recommended)* | 750 free hrs/mo (Auto-sleeps when inactive) | ❌ No | ~3 mins | ✅ Yes (Free SSL) |
| **Hugging Face Spaces** | 16 GB RAM, 2 vCPU (Completely Free forever) | ❌ No | ~2 mins | ✅ Yes (Free SSL) |
| **Koyeb** | 1 Free Micro Service | ❌ No | ~3 mins | ✅ Yes (Free SSL) |

> 🔒 **Why HTTPS Matters**: Modern browsers (Chrome, Safari, Edge, Firefox) **block camera access** unless the site is served over **`https://`** or `localhost`. Deploying on Render or Hugging Face provides a free trusted SSL certificate, allowing students and teachers to use the live camera scanner on any mobile phone, tablet, or laptop!

---

## 🟢 Option 1: Deploy on Render (Recommended)

Render is connected directly to your GitHub repository:
`https://github.com/sudarshanshinde6137-maker/ai-classroom-attendance-system`

### Step 1: Push your latest changes to GitHub
In your local project folder, commit and push the deployment files:
```bash
git add .
git commit -m "Add cloud deployment configuration (Dockerfile, Render, web requirements)"
git push origin main
```

### Step 2: Create a Free Web Service on Render
1. Open [Render.com](https://render.com) and sign in with your GitHub account.
2. Click **New +** in the top navigation bar and select **Web Service**.
3. Under **Connect a repository**, find and select `sudarshanshinde6137-maker/ai-classroom-attendance-system`.
4. Configure the service settings:
   - **Name**: `ai-attendance-studio` (or any name you prefer)
   - **Region**: Choose closest to you (e.g., `Singapore` or `Frankfurt` or `Oregon`)
   - **Branch**: `main`
   - **Runtime**: **Docker** *(Recommended: builds our optimized Dockerfile automatically)*
   - **Instance Type**: **Free** ($0/month)
5. Click **Deploy Web Service** at the bottom.

### Step 3: Access your Live App!
- Render will build the container and download the AI models (~2–3 minutes).
- Once live, you will see your public HTTPS URL (e.g., `https://ai-attendance-studio.onrender.com`).
- Open this URL on any phone, tablet, or PC to test live attendance, group photo processing, and student management!

---

## 🤗 Option 2: Deploy on Hugging Face Spaces (16 GB Free RAM)

Hugging Face Spaces provides 16 GB RAM and 2 vCPUs completely free without requiring a credit card.

### Step 1: Create a Space
1. Go to [Hugging Face Spaces](https://huggingface.co/spaces) and log in.
2. Click **Create new Space**.
3. Fill in:
   - **Space Name**: `ai-attendance-studio`
   - **License**: `mit` or `apache-2.0`
   - **Space SDK**: Select **Docker** (Blank)
   - **Space Hardware**: **Free (CPU basic • 2 vCPU • 16 GB)**
4. Click **Create Space**.

### Step 2: Push code to the Space
Hugging Face gives you a git repository for your Space. In your terminal:
```bash
# Add Hugging Face as a git remote
git remote add hf https://huggingface.co/spaces/<YOUR_USERNAME>/ai-attendance-studio

# Push your project
git push hf main
```
Hugging Face will automatically build the `Dockerfile`, launch on port `7860`, and your studio will be live in your browser!

---

## 🐳 Option 3: Run with Docker Compose (Local or VPS)

To run the production container locally or on a cloud virtual machine:

```bash
# Build and run in background
docker compose up --build -d

# Check logs
docker compose logs -f

# Stop the container
docker compose down
```
Access at: `http://localhost:8000`

---

## 🛠️ Files Added for Deployment

- [Dockerfile](file:///c:/Users/SUDHARSHAN/OneDrive/Desktop/attendance_system/Dockerfile): Production container with Python 3.11, OpenCV headless, and pre-cached YuNet + SFace ONNX models.
- [render.yaml](file:///c:/Users/SUDHARSHAN/OneDrive/Desktop/attendance_system/render.yaml): Render Blueprint for automated configuration.
- [requirements-web.txt](file:///c:/Users/SUDHARSHAN/OneDrive/Desktop/attendance_system/requirements-web.txt): Cloud dependencies optimized for Linux containers.
- [Procfile](file:///c:/Users/SUDHARSHAN/OneDrive/Desktop/attendance_system/Procfile): Process definition for PaaS platforms.
- [docker-compose.yml](file:///c:/Users/SUDHARSHAN/OneDrive/Desktop/attendance_system/docker-compose.yml): Multi-volume setup for persistent database and photos.
