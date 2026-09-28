import os
from datetime import datetime

from dotenv import load_dotenv
from langchain.tools import tool, ToolRuntime
from supabase import create_client

_ = load_dotenv()

client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


@tool
def shipping_tracker_tool(order_id: str, runtime: ToolRuntime) -> str:
    """Check the shipping status and estimated delivery date for an order."""
    try:
        parsed_id = int(order_id)
    except ValueError:
        return f"'{order_id}' doesn't look like a valid order ID -- please provide a numeric order ID."

    result = client.table("orders").select("*").eq("id", parsed_id).execute()
    if not result.data:
        return f"No order found with ID {order_id}."

    order = result.data[0]

    # Ownership check: only the logged-in customer's own orders are visible,
    # regardless of what order ID is asked for.
    user_email = runtime.config.get("configurable", {}).get("user_email")
    if user_email:
        customer = (
            client.table("customers").select("id").eq("email", user_email).execute()
        )
        current_customer_id = customer.data[0]["id"] if customer.data else None
        if current_customer_id is None or order["customer_id"] != current_customer_id:
            return "I can only provide shipping information for your own orders."

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
