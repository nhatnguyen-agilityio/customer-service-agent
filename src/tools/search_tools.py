from dotenv import load_dotenv
from langchain.tools import tool
from langchain_community.utilities import GoogleSerperAPIWrapper

_ = load_dotenv()

search = GoogleSerperAPIWrapper()


@tool
def web_search_tool(query: str) -> str:
    """Search the web for real-time information not available in the store's own database."""
    return search.run(query)
