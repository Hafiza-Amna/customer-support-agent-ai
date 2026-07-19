#!/bin/bash

# Start the ADK agent web server in the background
echo "Starting ADK Web Server on 127.0.0.1:8080..."
uv run adk web . --host 127.0.0.1 --port 8080 &

# Wait for the ADK server to start
sleep 5

# Start the Streamlit chatbot UI in the foreground on Hugging Face's port 7860
echo "Starting Streamlit Chat UI on 0.0.0.0:7860..."
uv run python -m streamlit run chatbot_ui.py --server.port 7860 --server.address 0.0.0.0
