import os
import psycopg

from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.postgres import PostgresSaver

from src.tools.price_tools import price_comparison_tool
from src.tools.shipping_tools import shipping_tracker_tool
from src.tools.search_tools import web_search_tool
from src.tools.rag_tools import faq_lookup_tool
from src.tools.sql_tools import get_sql_tools
from src.agent.memory import manage_memory
from src.agent.state import State
from src.agent.prompts import SYSTEM_PROMPT
from src.agent.errors import handle_tool_errors


# SQL toolkit connects eagerly at call time; if the DB is unreachable, degrade
# gracefully (agent still starts, just without DB-backed tools) instead of crashing.
try:
    SQL_TOOLS = get_sql_tools()
except Exception as e:
    print(
        f"[startup warning] SQL toolkit failed to initialize -- database queries unavailable: {e}"
    )
    SQL_TOOLS = []

ALL_TOOLS = SQL_TOOLS + [
    price_comparison_tool,
    web_search_tool,
    shipping_tracker_tool,
    faq_lookup_tool,
]

model  = init_chat_model("gpt-4o-mini").bind_tools(ALL_TOOLS)

def call_model(state: State) -> dict:
    """
    Call the model with the current state and return the model's response.
    """
    response = model.invoke(
        [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            *state["messages"]
        ]
    )
    return {"messages": [response]}

def route_after_model(state: State) -> str:
    """
    Determine the next step after the model's response.
    """
    last_message = state["messages"][-1]
    tool_calls = getattr(last_message, "tool_calls", None) or []
    return "tools" if len(tool_calls) > 0 else "end"

# Build the graph for the agent's state transitions
builder = (
    StateGraph(State)
    .add_node("manage_memory", manage_memory)
    .add_node("agent", call_model)
    .add_node("tools", ToolNode(ALL_TOOLS, wrap_tool_call=handle_tool_errors))
    .add_edge(START, "manage_memory")
    .add_edge("manage_memory", "agent")
    .add_conditional_edges(
        "agent", route_after_model, {"tools": "tools", "end": END}
    )
    .add_edge("tools", "agent")
)

# Compile the graph with a checkpointer (in-memory for now)
conn = psycopg.connect(os.environ["SUPABASE_DB_URL"], autocommit=True)
checkpointer = PostgresSaver(conn=conn)
checkpointer.setup()

graph = builder.compile(checkpointer=checkpointer)
