# API cURL Examples

Base URL: `http://localhost:8000`

---

## Health Check

```bash
curl -X GET http://localhost:8000/health
```

---

## Get Companies

Fetch distinct companies derived from the campaigns table.

```bash
curl -X GET http://localhost:8000/api/v1/companies
```

Expected response:
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174001",
    "name": "Test Company"
  }
]
```

---

## Get Active Campaigns for a Company

Fetch only active campaigns for a specific company.

```bash
curl -X GET "http://localhost:8000/api/v1/companies/123e4567-e89b-12d3-a456-426614174001/campaigns"
```

Expected response:
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "company_id": "123e4567-e89b-12d3-a456-426614174001",
    "company_name": "Test Company",
    "name": "Summer Sale",
    "description": "Summer promotional campaign",
    "theme": "Discount",
    "category": "Retail",
    "brand_voice": "Friendly and professional",
    "target_audience": "Young adults aged 18-35",
    "industry": "Technology",
    "status": "ACTIVE",
    "start_date": "2025-01-01T00:00:00",
    "end_date": "2025-12-31T23:59:59"
  }
]
```

---

## Admin UI

Access the Phase 1 admin UI at:

```
http://localhost:8000/static/admin.html
```

The UI provides:
- Company dropdown (derived from campaigns table)
- Campaign dropdown (active campaigns only)
- Topic selector (agriculture, sports, business, technologies, latest)
- Campaign details panel
- Generate button with 20-second polling (for local LLM)
- Suggestion list with checkboxes and news headlines
- Selected notifications area
- Publish button

---

## Create Notification Session (Async)

```bash
curl -X POST http://localhost:8000/api/v1/notification-sessions \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "sports",
    "campaign_id": "123e4567-e89b-12d3-a456-426614174000",
    "company_id": "123e4567-e89b-12d3-a456-426614174001",
    "admin_id": "22222222-2222-2222-2222-222222222222"
  }'
```

---

## Create Notification Session (Sync)

Equivalent to `test_ollama_llm_generates_notifications` in [`tests/test_agent_e2e.py`](tests/test_agent_e2e.py:13).

```bash
curl -X POST http://localhost:8000/api/v1/company/a639cab1-240b-4d66-b084-751009a88255/notification/sync \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "sports",
    "campaign_id": "3be6176f-894a-4c0b-87d1-83b9393fe8cb",
    "company_id": "a639cab1-240b-4d66-b084-751009a88255",
    "admin_id": "22222222-2222-2222-2222-222222222222"
  }'
```

Expected response includes:
- `all_suggestions` array with notification suggestions
- Each suggestion contains `id`, `notification_text`, `news_headline`, and `status`
- `conversation_history` array with valid JSON
- `status` set to `awaiting_review`

---

## Get Notification Session

```bash
curl -X GET "http://localhost:8000/api/v1/company/123e4567-e89b-12d3-a456-426614174001/notification-sessions/123e4567-e89b-12d3-a456-426614174000"
```

---

## Add Feedback to Session

```bash
curl -X POST "http://localhost:8000/api/v1/company/123e4567-e89b-12d3-a456-426614174001/notification-sessions/123e4567-e89b-12d3-a456-426614174000/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "feedback": "Make the notifications more urgent and include a discount code."
  }'
```

---

## Publish Selected Notifications

```bash
curl -X POST "http://localhost:8000/api/v1/company/123e4567-e89b-12d3-a456-426614174001/notification-sessions/123e4567-e89b-12d3-a456-426614174000/publish" \
  -H "Content-Type: application/json" \
  -d '{
    "selected_suggestion_ids": ["suggestion-id-1", "suggestion-id-2"]
  }'
```
