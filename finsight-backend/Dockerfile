# finsight-backend/Dockerfile
# ─────────────────────────────────────────────────────────────────
# Single stage — Python apps don't need a build/compile step.
# We just install dependencies and copy code.
#
# python:3.11-slim = Python 3.11 on Debian (minimal — no extras)
# WHY slim? Full python image is ~900MB. Slim is ~130MB.
# ─────────────────────────────────────────────────────────────────

FROM python:3.11-slim

# ── Environment variables ─────────────────────────────────────────
# PYTHONDONTWRITEBYTECODE=1  → don't create .pyc files (saves space)
# PYTHONUNBUFFERED=1         → print() shows in Docker logs immediately
#                              (without this logs are delayed/buffered)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_HOME=/app

WORKDIR $APP_HOME

# ── System dependencies ───────────────────────────────────────────
# build-essential: needed to compile some Python packages (rapidfuzz etc.)
# We clean up apt cache after to keep image small.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Python dependencies ───────────────────────────────────────────
# Copy requirements FIRST (before source code) for Docker layer caching.
# If requirements.txt didn't change → Docker skips pip install next time.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── App source code ───────────────────────────────────────────────
COPY . .

# ── Port ─────────────────────────────────────────────────────────
EXPOSE 8000

# ── Start command ─────────────────────────────────────────────────
# --host 0.0.0.0  → listen on all interfaces (not just localhost)
#                   WITHOUT this Docker container won't be reachable
# --port 8000     → match EXPOSE above
# NO --reload     → reload is for development only, not in containers
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
