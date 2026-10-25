# Production Dockerfile for AI Classroom Attendance Studio
# Compatible with Render, Hugging Face Spaces, Koyeb, Railway, and Docker

FROM python:3.11-slim

# Set environment flags
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    HOME=/app

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements-web.txt .
RUN pip install --no-cache-dir -r requirements-web.txt

# Copy project files
COPY . /app

# Ensure directories exist
RUN mkdir -p /app/database/models \
    /app/student_photos \
    /app/attendance_records \
    /app/reports \
    /app/temp

# Pre-download YuNet & SFace ONNX deep learning models during build
# This guarantees instant container startup with zero runtime download delays
RUN if [ ! -s /app/database/models/yunet.onnx ]; then \
        curl -L -o /app/database/models/yunet.onnx "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"; \
    fi && \
    if [ ! -s /app/database/models/sface.onnx ]; then \
        curl -L -o /app/database/models/sface.onnx "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx"; \
    fi

# Grant full read/write permissions for databases, uploads, and report generation
# (Essential for platforms like Hugging Face Spaces that run as non-root user 1000)
RUN chmod -R 777 /app

EXPOSE 8000 7860

# Launch FastAPI with dynamic port detection
CMD ["sh", "-c", "uvicorn web.server:app --host 0.0.0.0 --port ${PORT:-8000}"]
