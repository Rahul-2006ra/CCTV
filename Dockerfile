# ==========================================
# STAGE 1: Build Frontend (Vite + React SPA)
# ==========================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ==========================================
# STAGE 2: Python Backend & Unified Runner
# ==========================================
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860 \
    CCTV_MAX_SAMPLE_FRAMES=180 \
    CCTV_DATA_DIR=/app/data

# Install system dependencies: ffmpeg, ffprobe, graphics & system libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application source and documentation
COPY backend/ ./backend/
COPY docs/ ./docs/

# Copy compiled frontend from Stage 1 into frontend/dist
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create persistent storage directories
RUN mkdir -p /app/data/uploads /app/data/thumbnails /app/data/clips /app/data/qdrant

# Expose port 7860 (Hugging Face Spaces default)
EXPOSE 7860

# Start Uvicorn bound to 0.0.0.0 and dynamic $PORT (HF sets PORT=7860 automatically)
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
