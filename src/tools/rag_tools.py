import os

from dotenv import load_dotenv
from langchain.embeddings import init_embeddings
from langchain.tools import tool
from langchain_community.vectorstores import SupabaseVectorStore
from supabase import create_client

_ = load_dotenv()

client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])
embeddings = init_embeddings("openai:text-embedding-3-small")

faq_store = SupabaseVectorStore(
    client=client,
    embedding=embeddings,
    table_name="documents",
    query_name="match_documents",
)


@tool
def faq_lookup_tool(question: str) -> str:
    """Find the most relevant FAQ answer(s) for a customer's question about policies, shipping, returns, payment, etc."""
    matches = faq_store.similarity_search(question, k=3)
    if not matches:
        return "No relevant FAQ found for this question."
    return "\n\n".join(doc.page_content for doc in matches)
