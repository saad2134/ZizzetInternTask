# 🚀 Zizzet AI Lead Recovery Engine

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063.svg)](https://docs.pydantic.dev/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-20%20Passing-brightgreen.svg)]()

> **AI Backend Developer Intern — Technical Screening Submission**  
> An enterprise-grade, asynchronous FastAPI service that identifies inactive or high-intent leads, analyzes conversation histories using LLMs with structured Pydantic schema validation, and recommends the next best action and hyper-personalized follow-ups.

## 📑 Table of Contents
1. [Demo Video & Walkthrough](#-demo-video--walkthrough)
2. [Free Deployment: Live API & Swagger](#-free-deployment-live-api--swagger)
3. [Core Features & Highlights](#-core-features--highlights)
4. [Architecture & Pipeline Flow](#-architecture--pipeline-flow)
5. [Evaluation Test Cases (Cases A – E)](#-evaluation-test-cases-cases-a--e)
6. [Project Structure](#-project-structure)
7. [Quick Start & Setup](#-quick-start--setup)
   - [Local Development](#local-development)
   - [Docker & Docker Compose](#docker--docker-compose)
8. [Environment Variables](#-environment-variables)
9. [API Documentation & Examples](#-api-documentation--examples)
   - [`POST /api/v1/leads/analyze`](#1-post-apiv1leadsanalyze)
   - [`GET /api/v1/leads/{lead_id}/analysis`](#2-get-apiv1leadslead_idanalysis)
   - [`POST /api/v1/leads/{lead_id}/follow-up`](#3-post-apiv1leadslead_idfollow-up)
   - [`POST /api/v1/webhooks/leads`](#4-post-apiv1webhooksleads)
   - [`GET /api/v1/webhooks/jobs/{job_id}`](#5-get-apiv1webhooksjobsjob_id)
10. [Automated Testing & Coverage](#-automated-testing--coverage)
11. [Design Decisions, Assumptions & Limitations](#-design-decisions-assumptions--limitations)

---

## 🎥 Demo Video & Walkthrough

A high-definition 1080p demo video with synchronized voice-over narration is generated and included in the repository:
- **File**: [`demo_video.mp4`](demo_video.mp4)
- **Duration**: `02:20` (2 minutes 20 seconds — meeting the 2–3 minute submission target)
- **Covered Topics**:
  1. System Architecture & High-Level Pipeline
  2. Codebase Architecture & Modular Folder Structure
  3. Interactive Swagger / OpenAPI Documentation (`/docs`)
  4. Live Demonstration: Successful Recovery Analysis (Evaluation Cases A & C)
  5. Safety & Security: DNC Opt-Out Guardrails (Case D) and Multi-Tenant Isolation
  6. Asynchronous Webhooks & Idempotency Engine (Evaluation Case E)
  7. Automated Test Suite (20/20 tests passing) & Production Readiness

---

## 🌐 Free Deployment: Live API & Swagger

I have included pre-configured deployment manifests for 1-click free hosting on **Render**, **Railway**, **Koyeb**, or **Fly.io**:

### 1. Free Deployment on Render (1-Click Blueprint)
1. Fork or push this repository to GitHub.
2. Sign in to [Render.com](https://render.com/) (Free Tier available).
3. Click **New +** -> **Blueprint** and select your GitHub repository.
4. Render automatically detects [`render.yaml`](render.yaml) and deploys:
   - **Live Swagger UI**: `https://<your-app-name>.onrender.com/docs`
   - **Live Health Check**: `https://<your-app-name>.onrender.com/api/v1/health`
   - **Root Info**: `https://<your-app-name>.onrender.com/`

### 2. Free Deployment on Railway / Koyeb
1. Connect your GitHub repository to [Railway](https://railway.app/) or [Koyeb](https://www.koyeb.com/).
2. The service automatically reads [`Procfile`](Procfile) and [`Dockerfile`](Dockerfile).
3. Set environment variable: `LLM_PROVIDER=mock` (or your `OPENAI_API_KEY` / `GEMINI_API_KEY`).
4. Instant live HTTPS Swagger UI and API endpoints are available immediately at `/docs`.

---

## 🌟 Core Features & Highlights

- **🎯 Structured AI Recovery Recommendations**: Validates structured outputs strictly against Pydantic schemas (`lead_score`, `priority`, `intent`, `stage`, `summary`, `next_best_action`, `follow_up_channel`, `follow_up_message`, `do_not_contact`).
- **🛡️ Strict Multi-Tenant Isolation**: Enforces tenant boundary partitioning across all database tables, queries, headers (`X-Tenant-ID`), and endpoints. Prevents cross-tenant data leakage.
- **⚡ Async Webhooks with Idempotency**: Guarantees that duplicated webhook events or duplicate idempotency keys do not produce redundant processing jobs (Evaluation Case E).
- **🔌 Multi-Provider LLM Abstraction & Fallback**: Pluggable provider interface supporting **OpenAI (GPT-4o/mini)**, **Google Gemini (1.5-flash)**, **Ollama (local)**, and a **deterministic Mock Rule Engine** for offline development and instant CI/CD test execution.
- **🔁 Resilience & Exponential Backoff**: Uses `tenacity` exponential retry logic on external LLM calls and network operations.
- **📜 Prompt Versioning**: Centralized `PromptRegistry` supporting semantic prompt versions (`v1.0.0`, `v1.1.0`).
- **🛑 Strict Opt-Out (DNC) Compliance**: Automatic keyword and intent detection for "STOP", "don't message me again", and "unsubscribe". Sets `do_not_contact=True`, nulls out follow-up messages, and blocks outbound dispatch.
- **💬 Mock WhatsApp Provider Interface**: Simulated messaging client with message outbox tracking, delivery receipts, and validation.
- **📊 Duplicate Analysis Caching**: SHA-256 conversation hashing to prevent redundant LLM invocations on unmodified lead threads.
- **🔍 Observability & Structured JSON Logging**: Contextual request tracing via `X-Correlation-ID` and tenant tags across all log records.

---

## 🏗️ Architecture & Pipeline Flow

```
                      +-----------------------------+
                      |   Inbound Webhook / Client  |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |   FastAPI Gateway & Auth    |
                      |  - Request Validation       |
                      |  - Multi-Tenancy Check      |
                      |  - Correlation ID Injection |
                      +--------------+--------------+
                                     |
                    +----------------+----------------+
                    |                                 |
         [Synchronous Request]              [Async Webhook]
                    |                                 |
                    v                                 v
      +----------------------------+   +----------------------------+
      |      Analysis Service      |   |       Job Queue & DB       |
      |   (Cache & DNC Check)      |   |  - Idempotency Gate        |
      +-------------+--------------+   |  - Status: PENDING         |
                    |                  +--------------+-------------+
                    |                                 |
                    |                                 v
                    |                  +----------------------------+
                    |                  |      Lead Worker Task      |
                    |                  +--------------+-------------+
                    |                                 |
                    +----------------+----------------+
                                     |
                                     v
                      +-----------------------------+
                      |    LLM Provider Abstraction |
                      |    (Mock / OpenAI / Gemini) |
                      |    - Prompt Versioning      |
                      |    - Exponential Retry      |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      | Structured Output Validation|
                      | (Pydantic Schema Check)     |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |     PostgreSQL / SQLite     |
                      |  - Lead & Messages Persisted|
                      |  - Analysis Snapshot Stored |
                      |  - Job Status -> COMPLETED  |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |    Follow-Up / Mock Send    |
                      |   (WhatsApp Provider API)   |
                      +-----------------------------+
```

---

## 🧪 Evaluation Test Cases (Cases A – E)

| Case | Scenario | Expected Behavior | Status |
| :--- | :--- | :--- | :---: |
| **Case A** | 50 employees + asks for pricing | `priority: "high"`, `intent: "purchase"`, `lead_score >= 85` | ✅ Passed |
| **Case B** | Only asks what the product does | `priority: "low"`, `intent: "information"`, `lead_score < 50` | ✅ Passed |
| **Case C** | Requests a demo/call tomorrow | `next_best_action` prioritizes demo/call scheduling | ✅ Passed |
| **Case D** | Customer says: *"STOP. Don't message me again."* | `do_not_contact: true`, `follow_up_message: null`, blocked dispatch | ✅ Passed |
| **Case E** | Same webhook event submitted twice | One job created, duplicate detected, `is_duplicate: true` | ✅ Passed |

---

## 📁 Project Structure

```
ZizzetInternTask/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── health.py              # Health check & system info
│   │       │   ├── leads.py               # /leads/analyze, /analysis, /follow-up
│   │       │   └── webhooks.py            # /webhooks/leads, /jobs/{job_id}
│   │       └── api.py                     # Aggregated v1 API router
│   ├── core/
│   │   ├── config.py                      # Pydantic BaseSettings config
│   │   ├── exceptions.py                  # Domain exceptions & global error handlers
│   │   ├── logging.py                     # Structured JSON logging with contextvars
│   │   └── security.py                    # Multi-tenant header validation
│   ├── db/
│   │   ├── base.py                        # SQLAlchemy Declarative Base
│   │   └── session.py                     # Async engine & session lifecycle
│   ├── models/
│   │   ├── lead.py                        # Tenant, Customer, Lead, ConversationMessage
│   │   ├── analysis.py                    # LeadAnalysis record
│   │   ├── webhook.py                     # WebhookJob (idempotency tracking)
│   │   └── follow_up.py                   # FollowUpLog (messaging outbox)
│   ├── schemas/
│   │   ├── lead.py                        # Input schemas & conversation models
│   │   ├── analysis.py                    # RecoveryRecommendation & AnalysisResponse
│   │   ├── webhook.py                     # Webhook request & response schemas
│   │   └── follow_up.py                   # Follow-up request & response schemas
│   ├── services/
│   │   ├── lead_service.py                # Lead upsert & conversation hashing
│   │   ├── analysis_service.py            # Analysis orchestration & caching
│   │   ├── follow_up_service.py           # Follow-up generation & DNC guards
│   │   ├── llm/
│   │   │   ├── base.py                    # BaseLLMProvider ABC
│   │   │   ├── prompts.py                 # PromptRegistry (v1.0.0, v1.1.0)
│   │   │   ├── mock_provider.py           # Deterministic offline LLM engine
│   │   │   ├── openai_provider.py         # OpenAI GPT-4o integration
│   │   │   ├── gemini_provider.py         # Google Gemini integration
│   │   │   ├── ollama_provider.py         # Ollama local LLM integration
│   │   │   └── factory.py                 # Provider factory & fallback
│   │   └── messaging/
│   │       ├── base.py                    # BaseMessagingProvider ABC
│   │       └── mock_whatsapp.py          # Mock WhatsApp delivery provider
│   ├── workers/
│   │   ├── queue.py                       # In-memory async job queue
│   │   └── lead_worker.py                 # Background webhook worker task
│   └── main.py                            # FastAPI application entrypoint & lifespan
├── tests/
│   ├── conftest.py                        # Async test fixtures & in-memory DB
│   ├── test_analyze_api.py                # Core analysis & Evaluation Cases A-D
│   ├── test_caching_and_edge_cases.py     # Caching, 404s, health checks
│   ├── test_follow_up_api.py              # Follow-up dispatch & opt-out protection
│   ├── test_llm_providers.py              # LLM factory & prompt versioning
│   ├── test_multitenancy.py               # Strict tenant isolation verification
│   └── test_webhooks_idempotency.py       # Evaluation Case E & idempotency tests
├── demo_video.mp4                         # 1080p Demo video with voiceover narration
├── Dockerfile                             # Multi-stage production container
├── docker-compose.yml                     # PostgreSQL + API Orchestration
├── render.yaml                            # 1-Click Free Cloud Deployment
├── Procfile                               # Process file for cloud runners
├── pytest.ini                             # Pytest asyncio configuration
├── requirements.txt                       # Python dependencies
├── .env.example                           # Example environment template
├── .gitignore                             # Git ignore rules
└── README.md                              # Complete documentation
```

---

## 🚀 Quick Start & Setup

### Local Development

1. **Clone the repository:**
   ```bash
   git clone <repository_url>
   cd ZizzetInternTask
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   # On Linux/macOS:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment:**
   ```bash
   cp .env.example .env
   ```
   *(By default, `LLM_PROVIDER=mock` works instantly without any external API keys).*

5. **Start the FastAPI server:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

6. **Access the Interactive Swagger UI:**
   Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser.

---

### Docker & Docker Compose

To spin up the service with a full PostgreSQL database:

```bash
docker-compose up --build -d
```

- API Server: [http://localhost:8000](http://localhost:8000)
- Interactive Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

## ⚙️ Environment Variables

| Variable | Default | Description |
| :--- | :--- | :--- |
| `PROJECT_NAME` | `Zizzet AI Lead Recovery Engine` | Name of the service |
| `ENVIRONMENT` | `development` | Deployment environment (`development`, `production`) |
| `DATABASE_URL` | `sqlite+aiosqlite:///./zizzet_recovery.db` | Async database connection URL (SQLite or PostgreSQL) |
| `LLM_PROVIDER` | `mock` | Active LLM provider (`mock`, `openai`, `gemini`, `ollama`) |
| `OPENAI_API_KEY` | `""` | OpenAI API Key (required if `LLM_PROVIDER=openai`) |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model name |
| `GEMINI_API_KEY` | `""` | Google Gemini API Key (required if `LLM_PROVIDER=gemini`) |
| `GEMINI_MODEL` | `gemini-1.5-flash` | Gemini model name |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama service endpoint |
| `OLLAMA_MODEL` | `llama3` | Ollama model name |
| `PROMPT_VERSION` | `v1.0.0` | Active prompt version from `PromptRegistry` |
| `LLM_MAX_RETRIES` | `3` | Maximum retry attempts for LLM calls |
| `LLM_BACKOFF_FACTOR` | `1.5` | Exponential backoff multiplier for retries |
| `QUEUE_TYPE` | `in_memory` | Background queue backend (`in_memory` or `redis`) |
| `REQUIRE_TENANT_HEADER` | `false` | If `true`, enforces `X-Tenant-ID` header on all requests |

---

## 📡 API Documentation & Examples

### 1. `POST /api/v1/leads/analyze`
Analyzes a lead profile and conversation transcript synchronously and returns a structured AI recommendation.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/leads/analyze" \
     -H "Content-Type: application/json" \
     -d '{
       "tenant_id": "business_001",
       "lead_id": "lead_1024",
       "customer": {
         "name": "Arun Kumar",
         "phone": "+919876543210"
       },
       "lead": {
         "source": "whatsapp",
         "status": "contacted",
         "created_at": "2026-09-20",
         "last_contacted_at": "2026-09-25"
       },
       "conversation": [
         {"role": "customer", "message": "I am interested in your CRM."},
         {"role": "agent", "message": "How many users do you need?"},
         {"role": "customer", "message": "Around 25 users. What is the pricing?"}
       ]
     }'
```

**Response (200 OK):**
```json
{
  "lead_score": 86,
  "priority": "high",
  "intent": "purchase",
  "stage": "pricing_interest",
  "summary": "Customer is evaluating a CRM for a 25-member team.",
  "next_best_action": "Send pricing and schedule a demo",
  "follow_up_channel": "whatsapp",
  "follow_up_message": "Hi Arun! Just following up on your CRM requirement for 25 users. Here are the customized pricing tiers for your team size. Would you like a brief demo this week?",
  "do_not_contact": false,
  "tenant_id": "business_001",
  "lead_id": "lead_1024",
  "prompt_version": "v1.0.0",
  "model_used": "mock:mock-rule-engine-v1",
  "created_at": "2026-10-07T01:20:00.000Z"
}
```

---

### 2. `GET /api/v1/leads/{lead_id}/analysis`
Retrieves the latest persisted analysis for a lead. Supports multi-tenant isolation via `X-Tenant-ID` header or query parameter.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/leads/lead_1024/analysis?tenant_id=business_001" \
     -H "X-Tenant-ID: business_001"
```

---

### 3. `POST /api/v1/leads/{lead_id}/follow-up`
Generates a follow-up or dispatches it immediately via the mock WhatsApp provider.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/leads/lead_1024/follow-up?tenant_id=business_001" \
     -H "Content-Type: application/json" \
     -H "X-Tenant-ID: business_001" \
     -d '{
       "channel": "whatsapp",
       "send_immediately": true
     }'
```

**Response (200 OK):**
```json
{
  "success": true,
  "lead_id": "lead_1024",
  "tenant_id": "business_001",
  "channel": "whatsapp",
  "recipient_name": "Arun Kumar",
  "recipient_phone": "+919876543210",
  "follow_up_message": "Hi Arun! Just following up on your CRM requirement for 25 users. Here are the customized pricing tiers for your team size. Would you like a brief demo this week?",
  "do_not_contact": false,
  "status": "SENT",
  "provider_message_id": "wamid.4a7b9c1d8e2f0a1b"
}
```

*Note: If the lead has `do_not_contact=True`, the request returns `400 Bad Request` with an `OptOutError` and logs `BLOCKED_DNC`.*

---

### 4. `POST /api/v1/webhooks/leads`
Asynchronously receives lead webhook events, creates a tracking job, enforces idempotency, and schedules background processing.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/webhooks/leads" \
     -H "Content-Type: application/json" \
     -H "Idempotency-Key: evt_lead_1024_sync_1" \
     -d '{
       "tenant_id": "business_001",
       "lead_id": "lead_1024",
       "event_id": "evt_lead_1024_sync_1",
       "customer": {
         "name": "Arun Kumar",
         "phone": "+919876543210"
       },
       "lead": {
         "source": "whatsapp",
         "status": "contacted"
       },
       "conversation": [
         {"role": "customer", "message": "What is the pricing for 25 users?"}
       ]
     }'
```

**Response (202 Accepted):**
```json
{
  "success": true,
  "job_id": "job_a1b2c3d4e5f6",
  "tenant_id": "business_001",
  "lead_id": "lead_1024",
  "status": "PENDING",
  "is_duplicate": false,
  "message": "Webhook event accepted and queued for background AI recovery analysis.",
  "result": null
}
```

*If the same webhook payload or event ID is sent again, it returns `is_duplicate: true` and points to the existing job without duplicate reprocessing.*

---

### 5. `GET /api/v1/webhooks/jobs/{job_id}`
Checks the progress and structured result of an asynchronous webhook background job.

---

## 🧪 Automated Testing & Coverage

The test suite covers:
- Complete REST API endpoints (`/leads/analyze`, `/analysis`, `/follow-up`, `/webhooks/leads`, `/jobs`)
- All Evaluation Cases (**Case A, Case B, Case C, Case D, Case E**)
- Strict Multi-Tenant isolation & unauthorized cross-tenant blocking
- Idempotency & duplicate event detection
- DNC Opt-Out safety guardrails & blocked messaging attempts
- LLM Provider Factory, fallback logic, and prompt versioning

To run the full test suite with coverage:
```bash
pytest -v --cov=app --cov-report=term-missing
```

**Test Execution Result:**
```
============================= test session starts =============================
collected 20 items

tests/test_analyze_api.py::test_analyze_lead_pdf_example PASSED          [  5%]
tests/test_analyze_api.py::test_case_a_50_employees_pricing PASSED       [ 10%]
tests/test_analyze_api.py::test_case_b_only_asks_what_product_does PASSED [ 15%]
tests/test_analyze_api.py::test_case_c_requests_demo_call_tomorrow PASSED [ 20%]
tests/test_analyze_api.py::test_case_d_opt_out_stop PASSED               [ 25%]
tests/test_analyze_api.py::test_analyze_invalid_payload_validation PASSED [ 30%]
tests/test_caching_and_edge_cases.py::test_analysis_caching_behavior PASSED [ 35%]
tests/test_caching_and_edge_cases.py::test_get_nonexistent_lead_analysis PASSED [ 40%]
tests/test_caching_and_edge_cases.py::test_health_and_info_endpoints PASSED [ 45%]
tests/test_follow_up_api.py::test_follow_up_generation_and_dispatch PASSED [ 50%]
tests/test_follow_up_api.py::test_follow_up_blocked_on_opt_out_lead PASSED [ 55%]
tests/test_llm_providers.py::test_mock_llm_provider_direct PASSED        [ 60%]
tests/test_llm_providers.py::test_llm_factory_fallback PASSED            [ 65%]
tests/test_llm_providers.py::test_prompt_registry_versioning PASSED      [ 70%]
tests/test_multitenancy.py::test_tenant_isolation_get_analysis PASSED    [ 75%]
tests/test_multitenancy.py::test_tenant_mismatch_header_and_payload PASSED [ 80%]
tests/test_multitenancy.py::test_tenant_isolation_follow_up PASSED       [ 85%]
tests/test_webhooks_idempotency.py::test_case_e_webhook_idempotency_duplicate_submission PASSED [ 90%]
tests/test_webhooks_idempotency.py::test_webhook_idempotency_via_header PASSED [ 95%]
tests/test_webhooks_idempotency.py::test_get_webhook_job_status PASSED   [100%]

============================= 20 passed in 0.86s ==============================
```

---

## 📐 Design Decisions, Assumptions & Limitations

### Design Decisions:
1. **Multi-Tenancy at Core**: Every entity is scoped by `tenant_id`. Composite primary keys and foreign key constraints ensure strict database-level partitioning.
2. **Deterministic Dual-Layer Safety**: LLM prompts instruct the model to respect DNC opt-outs. As a secondary deterministic safeguard, code-level regex scanning enforces `do_not_contact=True` and strips `follow_up_message` to prevent LLM hallucinations from messaging opted-out leads.
3. **Pluggable Architecture**: LLM and messaging providers are abstracted through base interfaces (`BaseLLMProvider`, `BaseMessagingProvider`), allowing zero-code provider switching via configuration.
4. **Idempotency by Content & Key**: Webhook idempotency is supported either through explicit event IDs, `Idempotency-Key` headers, or SHA-256 conversation payload hashes.

### Assumptions:
- In production, database tables are hosted on PostgreSQL; local development default uses async SQLite for ease of evaluation.
- WhatsApp messaging is mocked via `MockWhatsAppProvider` with an in-memory outbox and database audit logs.

### Limitations:
- Background job processing in default mode runs in-memory via `asyncio.Queue`. In multi-instance cluster deployments, switching `QUEUE_TYPE=redis` with ARQ/Celery is recommended for distributed worker consumption.
