# AutoAssist AI - Production Deployment Guide

This guide details how to build, containerize, and deploy the **AutoAssist AI Web Platform & Diagnostic Analyzers** across various environments.

---

## 1. Quick Local Execution

### Option A: Windows Batch Launcher (Automated Browser Launch)
Double-click [`run_server.bat`](file:///c:/Users/anasa/OneDrive/Desktop/autoassistAI/run_server.bat) or run from PowerShell:
```powershell
.\run_server.bat
```
This automatically starts the FastAPI server on port 8000 and opens `http://127.0.0.1:8000/` in your browser.

### Option B: Python Virtual Environment / Conda
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Launch Uvicorn server
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
Open your browser at:
- **Web Diagnostic Dashboard**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Swagger Interactive API**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 2. Docker Container Deployment

The application includes a production-ready, lightweight Docker container with CPU-optimized ONNX Runtime.

### Build and Run with Docker
```bash
# 1. Build the Docker image
docker build -t autoassist-ai:latest .

# 2. Run container on port 8000
docker run -d \
  --name autoassist-ai \
  -p 8000:8000 \
  --restart unless-stopped \
  autoassist-ai:latest
```

### Build and Run with Docker Compose
```bash
docker compose up -d --build
```
To view live logs:
```bash
docker compose logs -f
```

---

## 3. Cloud Platform Deployment

### Render (Recommended for Free Cloud Hosting)
1. Fork or push this repository to GitHub.
2. In the [Render Dashboard](https://dashboard.render.com), click **New +** -> **Blueprint**.
3. Select this repository. Render will automatically detect [`render.yaml`](file:///c:/Users/anasa/OneDrive/Desktop/autoassistAI/render.yaml) and configure:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
   - Healthcheck: `/health`

### Railway / Fly.io / Heroku
The included [`Procfile`](file:///c:/Users/anasa/OneDrive/Desktop/autoassistAI/Procfile) and `Dockerfile` are automatically recognized:
```bash
# Deploy with Railway CLI
railway up

# Or deploy with Fly.io CLI
fly launch
fly deploy
```

---

## 4. Production Linux Server (Nginx + Systemd)

### Systemd Service Configuration
Create `/etc/systemd/system/autoassist.service`:
```ini
[Unit]
Description=AutoAssist AI Platform
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/autoassistAI
Environment="PATH=/var/www/autoassistAI/venv/bin"
ExecStart=/var/www/autoassistAI/venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

### Nginx Reverse Proxy Configuration
Add to `/etc/nginx/sites-available/autoassist`:
```nginx
server {
    listen 80;
    server_name autoassist.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/autoassistAI/backend/app/static/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }
}
```

---

## 5. Verification & Health Monitoring

Verify your deployment using cURL:
```bash
# Verify Health Endpoint
curl -s http://localhost:8000/health | jq .

# Verify Semantic RAG Search
curl -s -X POST http://localhost:8000/api/rag/search \
  -H "Content-Type: application/json" \
  -d '{"query": "engine overheating at idle", "top_k": 2}' | jq .

# Verify DTC Analyzer
curl -s -X POST http://localhost:8000/api/analyzers/dtc \
  -H "Content-Type: application/json" \
  -d '{"code": "P0300"}' | jq .
```
