import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase

_ = load_dotenv()


def get_sql_tools():
    """Build the SQL toolkit's tools (list-tables, schema, query, query-checker)."""
    db = SQLDatabase.from_uri(os.environ["SUPABASE_READONLY_DB_URL"])
    llm = init_chat_model("gpt-4o-mini")
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    # Four tools return from the toolkit: sql_db_list_tables, sql_db_schema, sql_db_query, sql_db_query_checker.
    return toolkit.get_tools()
