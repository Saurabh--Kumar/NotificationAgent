"""Prompt templates for the notification agent."""

NOTIFICATION_GENERATION_PROMPT = """Generate 3-5 engaging notification suggestions for the notification topic: {notification_topic}.
Company ID: {company_id}.

Use fetch_active_campaigns to get campaign details and fetch_news for context.

Note: The "topic" parameter in fetch_news refers to the news category (e.g., sports, business, technologies), 
not the notification topic. Use fetch_news to get relevant news articles that can inspire your notifications.

IMPORTANT: Your final notifications MUST be created around the news articles retrieved. 
Each notification should:
- Be short and catchy
- Be aligned with the campaign's brand voice and target audience
- Reference or incorporate insights from the news articles
- Be relevant to the notification topic: {notification_topic}

Return the suggestions as a JSON array of strings, e.g., ["notification 1", "notification 2", ...]"""