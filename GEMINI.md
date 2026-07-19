# Coding Agent Guide

## Prerequisites

Install the CLI (one-time):
```bash
uv tool install google-agents-cli
```

---

## Development Phases

### Phase 1: Understand Requirements
Before writing any code, understand the project's requirements, constraints, and success criteria.

### Phase 2: Build and Implement
Implement agent logic in `app/`. Use `agents-cli playground` for interactive testing. Iterate based on user feedback.

### Phase 3: The Evaluation Loop (Main Iteration Phase)
Start with 1-2 eval cases, run `agents-cli eval generate`, then `agents-cli eval grade`, iterate by making changes and rerunning both commands until satisfied.

### Phase 4: Pre-Deployment Tests
Run `uv run pytest tests/`. Fix issues until all tests pass.

---

## Development Commands

| Command | Purpose |
|---------|---------|
| `agents-cli playground` | Interactive local testing |
| `uv run pytest tests/` | Run unit tests |
| `agents-cli eval generate` | Run agent on eval dataset, produce traces |
| `agents-cli eval grade` | Run evaluations on traces |
| `agents-cli lint` | Check code quality |

---

## Operational Guidelines for Coding Agents

- **Code preservation**: Only modify code directly targeted by the user's request.
- **Groq tool calling**: Use `LiteLlm(model="groq/llama-3.3-70b-versatile")` wrapper and set `litellm.drop_params = True`.
- **ADK tool imports**: Import the tool instance, not the module.
- **Run Python with `uv`**: `uv run python script.py`.
- **Stop on repeated errors**: If the same error appears 3+ times, fix the root cause instead of retrying.
