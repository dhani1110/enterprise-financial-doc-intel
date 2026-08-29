# Minimal Dockerfile to run the FastAPI app
FROM python:3.11-slim

# system deps for psycopg2 and building some packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# set working dir
WORKDIR /app

# copy dependency lists first for caching
COPY requirements.txt .

# install python deps
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# copy app
COPY . /app

EXPOSE 8000

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
