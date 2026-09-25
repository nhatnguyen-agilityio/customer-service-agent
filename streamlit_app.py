import asyncio
import streamlit as st
from dotenv import load_dotenv

_ = load_dotenv()

from src.security.auth import login, sign_up
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
    return message["content"] if isinstance(message, dict) else message.content

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
        with st.spinner("Thinking..."):
            result = graph.invoke(
                {"messages": st.session_state.messages},
                config={
                    "configurable": {"thread_id": st.session_state.user_email}
                },
            )
            st.markdown(get_content(result["messages"][-1]))

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
