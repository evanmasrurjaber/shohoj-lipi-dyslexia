FROM python:3.10-slim

# Force Python to print logs immediately instead of buffering them
ENV PYTHONUNBUFFERED=1

# Install system dependencies as root
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Create a non-root user (Hugging Face Spaces runs containers as UID 1000)
RUN useradd -m -u 1000 user

# Switch to the "user" user
USER user

# Set home to the user's home directory so cache folders (~/.cache) are writable
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

# Copy requirements and install them as the user
COPY --chown=user backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY --chown=user backend/ backend/
COPY --chown=user ml/ ml/
COPY --chown=user data/ data/

EXPOSE 7860

CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
