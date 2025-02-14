FROM python:3.13-slim

# Install dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ .

# Create volume mount points
RUN mkdir -p /app/config
VOLUME ["/app/config"]

# Expose the port
EXPOSE 8080

# Set environment variables
ENV CONFIG_PATH=/app/config/users.yaml
ENV HOST=0.0.0.0
ENV PORT=8080

# Run the application
CMD ["uvicorn", "mock_login.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "8080"]
