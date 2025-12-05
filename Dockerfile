FROM python:3.12-slim

ARG DEBIAN_FRONTEND=noninteractive

# Install bubblewrap only (very lightweight)
RUN apt-get update && apt-get install -y --no-install-recommends \
    bubblewrap \
    ca-certificates \
    tzdata \
    build-essential \
    pkg-config \
    wget curl ca-certificates \
    openssl libssl-dev \
    zlib1g-dev \
    libncurses5-dev libncursesw5-dev \
    libreadline-dev \
    libsqlite3-dev \
    libgdbm-dev \
    libdb5.3-dev \
    libbz2-dev \
    libexpat1-dev \
    liblzma-dev \
    tk-dev \
    libffi-dev \
    uuid-dev \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/*

# Allow bubblewrap (user namespace sandbox)
RUN chmod u+s /usr/bin/bwrap

# Add non-root user
RUN useradd -m -u 1000 sandbox

WORKDIR /app

############################################
# Create lightweight venv for FastAPI server
############################################
RUN python3 -m venv /venv
ENV PATH="/venv/bin:$PATH"

# Install minimal dependencies for server (no cache)
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt \
    && find /venv -name '*.pyc' -delete \
    && find /venv -type d -name '__pycache__' -delete

COPY . .

RUN cd /app/packages/python/3.10.0/ && ./build.sh 3.10.0

RUN chown -R sandbox:sandbox /app

USER sandbox

EXPOSE 2000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -qO- http://127.0.0.1:2000/docs || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "2000"]
