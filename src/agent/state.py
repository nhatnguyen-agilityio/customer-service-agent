from typing_extensions import TypedDict, Annotated
from langgraph.graph.message import add_messages, AnyMessage

class State(TypedDict):
    """Input state for the agent."""

    messages: Annotated[list[AnyMessage], add_messages]
