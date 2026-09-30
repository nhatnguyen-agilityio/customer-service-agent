import os

import requests
from dotenv import load_dotenv
from langchain.tools import tool
from supabase import create_client

_ = load_dotenv()

client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


@tool
def price_comparison_tool(product_name: str) -> str:
    """Compare a product's price against real current market prices from other retailers."""
    result = (
        client.table("products")
        .select("name, price")
        .ilike("name", f"%{product_name}%")
        .limit(1)
        .execute()
    )
    if not result.data:
        return f"No product found matching '{product_name}'."

    product = result.data[0]
    our_price = float(product["price"])
    lines = [f"Our price for {product['name']}: ${our_price:.2f}"]

    response = requests.post(
        "https://google.serper.dev/shopping",
        headers={
            "X-API-KEY": os.environ["SERPER_API_KEY"],
            "Content-Type": "application/json",
        },
        json={"q": product["name"]},
        timeout=10,
    )
    response.raise_for_status()
    shopping_results = response.json().get("shopping", [])

    if not shopping_results:
        lines.append("No comparable market prices found for this product right now.")
        return "\n".join(lines)

    for item in shopping_results[:5]:
        source = item.get("source")
        price = item.get("price")
        if source and price:
            lines.append(f"{source}: {price}")

    return "\n".join(lines)
