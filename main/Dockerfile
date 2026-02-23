# WarCode — Django Online Judge Container
# Includes Python 3.12, g++ (C++), and OpenJDK (Java)

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system deps: g++ for C++, JDK for Java, coreutils for timeout
RUN apt-get update && apt-get install -y --no-install-recommends \
    g++ \
    default-jdk-headless \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME
ENV JAVA_HOME=/usr/lib/jvm/default-java
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# Verify compilers are installed (fails build early if not)
RUN echo "=== Compiler Verification ===" \
    && g++ --version | head -1 \
    && javac -version \
    && java -version 2>&1 | head -1 \
    && python3 --version \
    && echo "=== All compilers OK ==="

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Collect static files (during build — no DB needed for this)
RUN python manage.py collectstatic --noinput 2>/dev/null || true

EXPOSE 10000

# Start: run migrations then launch gunicorn
# Render injects $PORT (default 10000); we bind to 0.0.0.0:$PORT
CMD sh -c "python manage.py migrate --noinput && gunicorn main.wsgi:application --bind 0.0.0.0:\${PORT:-10000} --workers 3 --timeout 120"
