FROM node:24-bookworm

# Install Python environment
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install IBM Bob Shell from official release package
COPY bobshell.tgz /tmp/bobshell.tgz

RUN npm install -g /tmp/bobshell.tgz \
    && bob --version \
    && rm /tmp/bobshell.tgz

# Backend application
COPY app ./app

WORKDIR /app/app

# Render provides PORT
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]