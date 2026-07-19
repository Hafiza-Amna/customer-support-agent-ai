---
title: Customer Support Agent AI
emoji: 💬
colorFrom: pink
colorTo: purple
sdk: docker
pinned: false
---

# Customer Support Agent AI

## Project Overview
Customer Support Agent AI is an intelligent conversational assistant built to handle customer inquiries about shipping, policies, and orders. Powered by the Google Agent Development Kit (ADK) and Groq's `llama-3.3-70b-versatile` model, the agent uses structured tools to provide accurate, real-time responses to customer queries for a simulated e-commerce platform.

## Features
- **Intelligent Tool Use:** Dynamically selects and calls Python tools (e.g., `get_shipping_rates`, `get_return_policy`, `check_order_status`).
- **Interactive Conversational UI:** Pre-configured with the ADK Dev UI for easy testing and demonstrations.
- **Fast Inference:** Built on Groq's high-speed inference engine.
- **Production-Ready Structure:** Uses ADK workflows and configurations suitable for cloud deployments.

## Tech Stack
- **Python:** 3.11+
- **Google ADK (Agent Development Kit):** Framework for defining tools and agents.
- **LiteLLM:** Provides unified LLM routing.
- **Groq API:** Hosting the `llama-3.3-70b-versatile` model.
- **FastAPI / Uvicorn:** Under the hood for ADK web server.

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/HafizaAmnaNaseem/customer-support-agent-ai.git
   cd customer-support-agent-ai
   ```

2. **Set up the virtual environment:**
   Using `uv` (recommended) or standard `pip`:
   ```bash
   uv sync
   # or
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

## Environment Variables
Create a `.env` file in the root of the project:
```env
GROQ_API_KEY="your_groq_api_key_here"
```

## Groq API Setup
To run this project, you need an API key from Groq:
1. Go to [Groq Console](https://console.groq.com/).
2. Create an account and generate a new API key.
3. Add the key to your `.env` file.

## Local Run Instructions

**Option 1 — Use the included batch script (recommended on Windows):**
```bat
.\run_customer.bat
```

**Option 2 — Run manually from the terminal:**
```bash
uv run python -m google.adk.cli web . --host 127.0.0.1 --port 8001
```

Then open your browser and go to: **http://127.0.0.1:8001/dev-ui**

## Usage Examples
In the ADK Dev UI chat, you can ask:
- *"What are your shipping rates?"*
- *"Can I return a product I bought 40 days ago?"*
- *"What is the status of my order #12345?"*

## Project Structure
```
customer-support-agent-ai/
├── app/
│   ├── __init__.py
│   └── agent.py       # Core Agent and Tool definitions
├── pyproject.toml     # Dependencies and project metadata
├── .env.example       # Example environment variables
└── README.md
```

## Future Improvements
- Connect `check_order_status` to a real PostgreSQL or MongoDB database.
- Implement session persistence across restarts.
- Deploy to Hugging Face or Google Cloud Run.

## License
MIT License

## Author
Hafiza Amna

## Live Demo
- [Hugging Face Space](https://huggingface.co/spaces/1Hafiza-Amna7/customer-support-agent-ai)
