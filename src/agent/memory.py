from langchain_core.messages import trim_messages
from langchain.chat_models import init_chat_model
from src.agent.state import State

def manage_memory(state: State) -> dict:
    """
    This function will manage the memory of the agent.
    """
    
    trimmed = trim_messages(
        state["messages"],
        max_tokens=4000,
        strategy="last",
        token_counter=init_chat_model("gpt-4o-mini"),
        start_on="human",
    )
    if len(trimmed) == len(state["messages"]):
        return {}  # nothing trimmed, no update needed
    return {"messages": trimmed}
