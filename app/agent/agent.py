from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, ToolMessage
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
import operator
from app.agent.tools import fetch_active_campaigns, fetch_news
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

    for tool_call in tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_id = tool_call["id"]

        if tool_name == "fetch_active_campaigns":
            result = fetch_active_campaigns.invoke(tool_args)
        elif tool_name == "fetch_news":
            result = fetch_news.invoke(tool_args)
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
    """Invoke the agent to generate notification suggestions for a given topic."""
    initial_message = HumanMessage(
        content=f"Generate 3-5 engaging notification suggestions for the topic: {topic}. "
        "Use fetch_active_campaigns to get campaign details and fetch_news for context. "
        "Each notification should be short, catchy, and aligned with the campaign's brand voice and target audience."
    )
    state = {
        "messages": [initial_message],
        "company_id": company_id,
        "topic": topic,
    }
    result = notification_agent.invoke(state)
    return result["messages"]
