#!/usr/bin/env bash
set -o errexit

# -------------------------------------------------------
# Render Build Script
# Works for BOTH Docker and Native Python deployments.
# Installs g++ and JDK so C++ and Java submissions work.
# -------------------------------------------------------

# Install system dependencies for C++ and Java compilation
apt-get update && apt-get install -y --no-install-recommends \
    g++ \
    default-jdk-headless

# Set JAVA_HOME if not already set
export JAVA_HOME=${JAVA_HOME:-/usr/lib/jvm/default-java}
export PATH="${JAVA_HOME}/bin:${PATH}"

# Verify compilers are accessible
echo "=== Verifying compilers ==="
g++ --version || echo "WARNING: g++ not found!"
javac -version || echo "WARNING: javac not found!"
java -version || echo "WARNING: java not found!"
echo "=== Compiler verification complete ==="

# Install Python dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Run database migrations
python manage.py migrate
