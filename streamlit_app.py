import asyncio
import streamlit as st
from dotenv import load_dotenv

_ = load_dotenv()

from src.security.auth import login, sign_up
from src.security.rate_limit import check_and_increment
from src.agent.graph import graph

st.set_page_config(page_title="Customer Service Agent", page_icon="🤖")

if "user_email" not in st.session_state:
    st.session_state.user_email = None

if "access_token" not in st.session_state:
    st.session_state.access_token = None

if "messages" not in st.session_state:
    st.session_state.messages = []

# Sign up, login form
def show_auth_form():
    st.title("Customer Service Agent")
    mode = st.radio("", ["Log In", "Sign Up"], horizontal=True)
    st.write("Please log in or sign up to continue.")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    
    if st.button(mode):
        try:
            if mode == "Log In":
                token = asyncio.run(login(email, password))
            else:
                asyncio.run(sign_up(email, password))
                token = asyncio.run(login(email, password))
        except Exception:
            st.error("Authentication failed. Please check your credentials and try again.")
            return
        
        st.session_state.access_token = token
        st.session_state.user_email = email
        st.rerun()

# Handle show sign up, login form if not logged in
if not st.session_state.user_email:
    show_auth_form()
    st.stop()

def get_role(message) -> str:
    if isinstance(message, dict):
        return message["role"]
    return {"human": "user", "ai": "assistant"}.get(message.type, message.type)

def get_content(message) -> str:
    content = message["content"] if isinstance(message, dict) else message.content
    # Escape literal "$" so Streamlit's markdown renderer doesn't interpret
    # price mentions (e.g. "$5.99 ... $50") as a LaTeX math expression.
    return content.replace("$", "\\$")

def is_visible_message(message) -> bool:
    """Only show real user turns and final assistant replies."""
    if isinstance(message, dict):
        return bool(message.get("content"))
    if message.type == "tool":
        return False
    if message.type == "ai" and not message.content:
        return False
    return message.type in ("human", "ai")

@st.cache_resource
def load_graph():
    return graph

graph = load_graph()

# Load chat history from session state
if "history_loaded" not in st.session_state:
    config = {"configurable": {"thread_id": st.session_state.user_email}}
    snapshot = graph.get_state(config)
    st.session_state.messages = snapshot.values.get("messages", [])
    st.session_state.history_loaded = True

st.title("🤖 Customer Service Agent")

if not st.session_state.messages:
    st.info(
        "Ask me about product details, prices, order status, returns, or anything else "
        "I can help with!"
    )

for message in st.session_state.messages:
    if not is_visible_message(message):
        continue
    with st.chat_message(get_role(message)):
        st.write(get_content(message))


if user_input := st.chat_input("How can I help you today?"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        if not check_and_increment(st.session_state.user_email):
            st.warning(
                "You've sent a lot of messages recently -- please wait a bit "
                "before sending more."
            )
            result = None
        else:
            with st.spinner("Thinking..."):
                try:
                    result = graph.invoke(
                        {"messages": st.session_state.messages},
                        config={
                            "configurable": {
                                "thread_id": st.session_state.user_email,
                                "user_email": st.session_state.user_email,
                            }
                        },
                    )
                except Exception as e:
                    print(f"[streamlit_app] graph.invoke failed: {e}")
                    st.error(
                        "Something went wrong on our end and I couldn't process that. "
                        "Please try again in a moment."
                    )
                    result = None

                if result is not None:
                    st.markdown(get_content(result["messages"][-1]))

    if result is not None:
        st.session_state.messages = result["messages"]

with st.sidebar:
    st.markdown("### 🤖 Customer Service Agent")
    st.caption(f"Logged in as **{st.session_state.user_email}**")
    st.divider()
    if st.button("Log out"):
        st.session_state.user_email = None
        st.session_state.access_token = None
        st.session_state.messages = []
        st.session_state.history_loaded = False
        st.rerun()
