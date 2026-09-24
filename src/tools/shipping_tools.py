import os
from datetime import datetime

from dotenv import load_dotenv
from langchain.tools import tool
from supabase import create_client

_ = load_dotenv()

client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


@tool
def shipping_tracker_tool(order_id: str) -> str:
    """Check the shipping status and estimated delivery date for an order."""
    try:
        parsed_id = int(order_id)
    except ValueError:
        return f"'{order_id}' doesn't look like a valid order ID -- please provide a numeric order ID."

    result = client.table("orders").select("*").eq("id", parsed_id).execute()
    if not result.data:
        return f"No order found with ID {order_id}."

    order = result.data[0]
    status = order["status"]

    if status == "delivered":
        return f"Order {order_id} has been delivered."

    eta_raw = order.get("estimated_delivery")
    if not eta_raw:
        return f"Order {order_id} is currently '{status}'. No delivery estimate available yet."

    eta = datetime.fromisoformat(eta_raw)
    return (
        f"Order {order_id} is currently '{status}'. "
        f"Estimated delivery: {eta.strftime('%Y-%m-%d')}."
    )
