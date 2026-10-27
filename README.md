# Example Bank Complaint Triage

A FastAPI service that uses a live OpenAI-compatible LLM to classify bank complaints and route them to the appropriate support team. The service validates model output against a strict Pydantic contract and falls back to human review when the model times out or returns invalid JSON.

## Requirements

- Python 3.11 or later
- [Ollama](https://ollama.com/) installed and running
- The `gemma3:1b` model
- A virtual environment

## Setup

Clone or open this project, then create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Create local environment configuration:

```powershell
Copy-Item .env.example .env
```

Download the model if you have not already:

```powershell
ollama pull gemma3:1b
```

Ollama should be running locally at `http://localhost:11434`. No API key is needed.

## Run the API

```powershell
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open the interactive API documentation at:

- Swagger UI: http://localhost:8000/docs
- Health check: http://localhost:8000/healthz

## Configuration

| Variable | Required | Default | Description |
|---|---:|---|---|
| `LLM_MODEL` | No | `gemma3:1b` | Ollama model identifier |
| `LLM_BASE_URL` | No | `http://localhost:11434/v1` | Ollama OpenAI-compatible API URL |
| `TRIAGE_TIMEOUT_S` | No | `5` | Maximum total triage request time |

## API

### `GET /healthz`

Returns service health:

```json
{
  "status": "ok"
}
```

### `POST /triage`

Example request:

```json
{
  "id": "C-004",
  "text": "Why was a minimum balance penalty fee deducted this month? I kept the balance above the limit.",
  "channel": "email"
}
```

Example model-routed response:

```json
{
  "category": "charges",
  "priority": 3,
  "team": "branch_services",
  "summary": "Customer disputes an unexpected minimum balance penalty fee.",
  "needs_human": false
}
```

Allowed values:

- Categories: `card_dispute`, `fraud`, `account_access`, `charges`, `other`
- Teams: `disputes`, `fraud_ops`, `digital_support`, `branch_services`, `human_review`
- Priority: integer from `1` through `4`
- `needs_human`: boolean

If the model call times out or produces invalid output, the API returns an `other` result routed to `human_review`.

## Request logging

Every request emits one JSON log entry containing:

- request ID
- route
- HTTP status
- latency
- model and prompt version
- routing outcome
- a short complaint excerpt

The configured JSON formatter masks account numbers matching `EB-##########` before outputting them.

## Sample data

The `data/complaints.jsonl` file contains example complaint records for manual testing.

## Security

- Never commit `.env` or real API keys.
- Keep `.env.example` free of credentials.
- Rotate keys that have been exposed publicly.
- Use provider-side API restrictions and billing alerts.
