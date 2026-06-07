"""Prompt templates for the notification agent."""

NOTIFICATION_GENERATION_PROMPT = """Generate 3-5 engaging notification suggestions.

First, call fetch_active_campaigns with company_id="{company_id}" to get campaign details.
Then, call fetch_news to get relevant news articles.

IMPORTANT: Your final notifications MUST be created around the news articles retrieved. Each notification should:
- Be short and catchy
- Be aligned with the campaign's brand voice and target audience
- Reference or incorporate insights from the news articles
- Incorporate the campaign's theme, category, and industry
- Match the brand voice (e.g., trendy, professional, friendly)
- Target the specified audience

Campaign data you will receive from fetch_active_campaigns includes:
- company_name: The company running the campaign
- name: The campaign name
- description: Campaign description
- theme: The campaign theme
- category: The campaign category
- brand_voice: The brand voice/style to use
- target_audience: Who the notifications are targeting
- industry: The industry sector

Use these campaign fields to tailor each notification appropriately.

Note: The "topic" parameter in fetch_news refers to the news category (e.g., sports, business, technologies).
Use fetch_news to get relevant news articles that can inspire your notifications.

Return the suggestions as a JSON array of pairs, where each pair is [notification_text, news_headline], e.g., 
[["notification 1", "related news headline 1"], ["notification 2", "related news headline 2"], ...]"""