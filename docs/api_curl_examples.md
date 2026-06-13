# API cURL Examples

Base URL: `http://localhost:8000`

---

## Health Check

```bash
curl -X GET http://localhost:8000/health
```

---

## Create Notification Session (Async)

```bash
curl -X POST http://localhost:8000/api/v1/notification-sessions \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Summer Sale",
    "campaign_id": "123e4567-e89b-12d3-a456-426614174000",
    "company_id": "123e4567-e89b-12d3-a456-426614174001",
    "admin_id": "123e4567-e89b-12d3-a456-426614174002"
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
