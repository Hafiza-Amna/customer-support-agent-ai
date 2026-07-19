# Use lightweight Python base image
FROM python:3.12-slim

# Install uv package manager
RUN pip install --no-cache-dir uv==0.8.13

# Set the working directory inside the container
WORKDIR /code

# Copy dependency definition files
COPY ./pyproject.toml ./README.md ./uv.lock* ./

# Sync dependencies (including Streamlit) using uv
RUN uv sync --frozen

# Copy the rest of the application files
COPY ./app ./app
COPY ./chatbot_ui.py ./chatbot_ui.py
COPY ./start.sh ./start.sh

# Convert Windows line endings (CRLF) to Linux format (LF) for start.sh and make it executable
RUN apt-get update && apt-get install -y --no-install-recommends sed \
    && sed -i 's/\r$//' ./start.sh \
    && chmod +x ./start.sh \
    && apt-get purge -y --auto-remove sed \
    && rm -rf /var/lib/apt/lists/*

# Expose Hugging Face's default web interface port
EXPOSE 7860

# Run the startup script which launches both the ADK agent and Streamlit UI
CMD ["./start.sh"]
