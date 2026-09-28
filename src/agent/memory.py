from langchain_core.messages import trim_messages, RemoveMessage
from langchain.chat_models import init_chat_model
from src.agent.state import State

def manage_memory(state: State) -> dict:
    """
    Trim old messages once the conversation passes a token threshold.
    """
    trimmed = trim_messages(
        state["messages"],
        max_tokens=4000,
        strategy="last",
        token_counter=init_chat_model("gpt-4o-mini"),
        start_on="human",
    )
    if len(trimmed) == len(state["messages"]):
        return {}  # nothing to trim

    kept_ids = {m.id for m in trimmed}
    to_remove = [
        RemoveMessage(id=m.id) for m in state["messages"] if m.id not in kept_ids
    ]
    return {"messages": to_remove}
