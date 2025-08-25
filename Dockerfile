# 1. Base Image
FROM python:3.11-slim

# 2. Set Environment Variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Set Workdir
WORKDIR /app

# 4. Install Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install ffmpeg for audio conversion
RUN apt-get update && apt-get install -y ffmpeg

# 5. Copy Application Code
COPY src/ .

# 6. Expose Port and Run Application
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
