import os
import random

from dotenv import load_dotenv
from langchain.tools import tool
from supabase import create_client

_ = load_dotenv()

client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])

# Simulated competitor names. Replace this whole block with a real
COMPETITORS = ["CompetitorMart", "ShopFast", "ValueGoods"]


@tool
def price_comparison_tool(product_name: str) -> str:
    """Compare a product's price against a few competitor prices."""
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
    for competitor in COMPETITORS:
        variance = random.uniform(-0.15, 0.15)
        competitor_price = round(our_price * (1 + variance), 2)
        lines.append(f"{competitor}: ${competitor_price:.2f}")

    return "\n".join(lines)
