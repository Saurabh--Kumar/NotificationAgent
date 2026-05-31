"""Prompt templates for the notification agent."""

NOTIFICATION_GENERATION_PROMPT = """Generate 3-5 engaging notification suggestions for the topic: {topic}.
Company ID: {company_id}.

Use fetch_active_campaigns to get campaign details and fetch_news for context.

IMPORTANT: Your final notifications MUST be created around the news articles retrieved. 
Each notification should:
- Be short and catchy
- Be aligned with the campaign's brand voice and target audience
- Reference or incorporate insights from the news articles
- Be relevant to the topic: {topic}

Return the suggestions as a JSON array of strings, e.g., ["notification 1", "notification 2", ...]"""