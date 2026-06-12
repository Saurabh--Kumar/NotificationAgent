import logging
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, ToolMessage
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
import operator
from app.agent.tools import fetch_active_campaigns, fetch_news
from app.agent.prompts import NOTIFICATION_GENERATION_PROMPT
from app.core.config import settings


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    company_id: str | None
    topic: str | None


# Initialize Ollama LLM (local gemma4:e2b)
llm = ChatOllama(
    model=settings.OLLAMA_MODEL,
    base_url=settings.OLLAMA_BASE_URL,
    temperature=0.7,
)
llm_with_tools = llm.bind_tools([fetch_active_campaigns, fetch_news])


def agent_node(state: AgentState):
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def tools_node(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    tool_calls = getattr(last_message, "tool_calls", [])
    tool_messages = []
    company_id = state.get("company_id")

    for tool_call in tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_id = tool_call["id"]

        # Inject company_id from state if the tool accepts it
        if tool_name == "fetch_active_campaigns":
            if company_id and "company_id" not in tool_args:
                tool_args = {**tool_args, "company_id": company_id}
            result = fetch_active_campaigns.invoke(tool_args)
            logging.info(f"module=app.agent.agent method=tools_node message=Invoked fetch_active_campaigns for company_id: {company_id}")
        elif tool_name == "fetch_news":
            result = fetch_news.invoke(tool_args)
            logging.info(f"module=app.agent.agent method=tools_node message=Invoked fetch_news with args: {tool_args}")
        else:
            result = "Unknown tool"

        tool_messages.append(ToolMessage(content=str(result), tool_call_id=tool_id))

    return {"messages": tool_messages}


def should_continue(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    if getattr(last_message, "tool_calls", None):
        return "tools"
    return END


# Build LangGraph workflow
workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", tools_node)
workflow.set_entry_point("agent")
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {"tools": "tools", END: END}
)
workflow.add_edge("tools", "agent")

notification_agent = workflow.compile()


def generate_notifications(topic: str, company_id: str | None = None) -> list:
    """Invoke the agent to generate notification suggestions for a given topic.
    
    Returns:
        List of pairs [notification_text, news_headline] for each suggestion.
    """
    logging.info(f"module=app.agent.agent method=generate_notifications message=Starting notification generation for topic: {topic}")
    
    initial_message = HumanMessage(
        content=NOTIFICATION_GENERATION_PROMPT.format(notification_topic=topic, company_id=company_id)
    )
    state = {
        "messages": [initial_message],
        "company_id": company_id,
        "topic": topic,
    }
    result = notification_agent.invoke(state)
    # Return only the last message content (the actual notification suggestions)
    messages = result["messages"]
    if messages:
        last_message = messages[-1]
        content = getattr(last_message, "content", str(last_message))
        # Try to parse as JSON, fall back to string if not valid JSON
        import json
        import re
        
        def extract_validated_suggestions(parsed):
            if isinstance(parsed, list):
                validated = []
                for item in parsed:
                    if isinstance(item, list) and len(item) == 2:
                        validated.append([str(item[0]), str(item[1])])
                    elif isinstance(item, str):
                        validated.append([item, ""])
                return validated
            return None
        
        def clean_json_string(s):
            # Remove trailing commas before ] or }
            s = re.sub(r',\s*([\]\}])', r'\1', s)
            # Remove markdown code block markers
            s = re.sub(r'```(?:json)?\s*', '', s)
            s = re.sub(r'\s*```', '', s)
            s = re.sub(r'``(?:json)?\s*', '', s)
            s = re.sub(r'\s*``', '', s)
            s = re.sub(r'`(?:json)?\s*', '', s)
            s = re.sub(r'\s*`', '', s)
            return s.strip()
        
        # Strategy 1: Try to parse the entire content as JSON
        try:
            parsed = json.loads(content)
            validated = extract_validated_suggestions(parsed)
            if validated is not None:
                logging.info(f"module=app.agent.agent method=generate_notifications message=Generated {len(validated)} suggestions")
                return validated
        except (json.JSONDecodeError, TypeError):
            pass
        
        # Strategy 2: Try to find a JSON array within the text
        start = content.find('[')
        end = content.rfind(']')
        if start != -1 and end != -1 and end > start:
            try:
                json_str = clean_json_string(content[start:end+1])
                parsed = json.loads(json_str)
                validated = extract_validated_suggestions(parsed)
                if validated is not None:
                    logging.info(f"module=app.agent.agent method=generate_notifications message=Generated {len(validated)} suggestions")
                    return validated
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Strategy 3: Clean the entire content and try to parse
        try:
            cleaned = clean_json_string(content)
            parsed = json.loads(cleaned)
            validated = extract_validated_suggestions(parsed)
            if validated is not None:
                logging.info(f"module=app.agent.agent method=generate_notifications message=Generated {len(validated)} suggestions")
                return validated
        except (json.JSONDecodeError, TypeError):
            pass
        
        logging.info(f"module=app.agent.agent method=generate_notifications message=Generated 1 suggestion (fallback format)")
        return [[content, ""]] if content else []
    return []
