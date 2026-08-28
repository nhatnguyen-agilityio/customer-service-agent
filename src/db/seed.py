"""Seed synthetic products, customers, orders, and FAQs into Supabase.

Run once after applying src/db/schema.sql:
    uv run python src/db/seed.py
"""

import os
import random
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from langchain.embeddings import init_embeddings
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_core.documents import Document
from supabase import create_client

_ = load_dotenv()

random.seed(42)  # reproducible seed data across runs

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

PRODUCTS = [
    # Electronics
    {"name": "Wireless Bluetooth Headphones", "category": "Electronics", "description": "Over-ear headphones with active noise cancellation and 30-hour battery life.", "price": 89.99, "stock_qty": 42},
    {"name": "Portable Power Bank 20000mAh", "category": "Electronics", "description": "Fast-charging power bank with USB-C and dual USB-A output.", "price": 34.99, "stock_qty": 75},
    {"name": "4K Streaming Media Player", "category": "Electronics", "description": "Compact streaming stick supporting 4K HDR and voice remote.", "price": 49.99, "stock_qty": 30},
    {"name": "Mechanical Keyboard - RGB", "category": "Electronics", "description": "Tactile mechanical keyboard with per-key RGB lighting.", "price": 74.99, "stock_qty": 20},
    {"name": "Wireless Ergonomic Mouse", "category": "Electronics", "description": "Ergonomic wireless mouse designed to reduce wrist strain.", "price": 29.99, "stock_qty": 60},
    {"name": "Smart Home Speaker", "category": "Electronics", "description": "Voice-controlled smart speaker with premium sound.", "price": 59.99, "stock_qty": 25},
    {"name": "USB-C Multiport Hub", "category": "Electronics", "description": "7-in-1 USB-C hub with HDMI, SD card reader, and 100W passthrough.", "price": 39.99, "stock_qty": 50},
    {"name": "Noise-Cancelling Earbuds", "category": "Electronics", "description": "True wireless earbuds with adaptive noise cancellation.", "price": 119.99, "stock_qty": 18},
    {"name": "Laptop Stand - Adjustable", "category": "Electronics", "description": "Aluminum laptop stand with adjustable height and angle.", "price": 27.99, "stock_qty": 45},
    # Home & Kitchen
    {"name": "Stainless Steel Water Bottle", "category": "Home & Kitchen", "description": "Insulated 32oz water bottle, keeps drinks cold for 24 hours.", "price": 24.99, "stock_qty": 90},
    {"name": "Programmable Coffee Maker", "category": "Home & Kitchen", "description": "12-cup programmable coffee maker with auto shut-off.", "price": 44.99, "stock_qty": 22},
    {"name": "Cast Iron Skillet 10-inch", "category": "Home & Kitchen", "description": "Pre-seasoned cast iron skillet, oven safe up to 500F.", "price": 32.99, "stock_qty": 35},
    {"name": "Knife Set with Block", "category": "Home & Kitchen", "description": "6-piece stainless steel kitchen knife set with wooden block.", "price": 69.99, "stock_qty": 15},
    {"name": "Robot Vacuum Cleaner", "category": "Home & Kitchen", "description": "Smart robot vacuum with app control and auto-recharge.", "price": 199.99, "stock_qty": 12},
    {"name": "Bamboo Cutting Board Set", "category": "Home & Kitchen", "description": "3-piece bamboo cutting board set, various sizes.", "price": 19.99, "stock_qty": 55},
    {"name": "Air Fryer 5.8-Quart", "category": "Home & Kitchen", "description": "Digital air fryer with 8 preset cooking modes.", "price": 79.99, "stock_qty": 28},
    {"name": "Memory Foam Pillow", "category": "Home & Kitchen", "description": "Contoured memory foam pillow for neck support.", "price": 29.99, "stock_qty": 40},
    # Sports & Outdoors
    {"name": "Yoga Mat - Non-Slip", "category": "Sports & Outdoors", "description": "Extra-thick non-slip yoga mat with carrying strap.", "price": 22.99, "stock_qty": 65},
    {"name": "Adjustable Dumbbell Set", "category": "Sports & Outdoors", "description": "Pair of adjustable dumbbells, 5-25 lbs each.", "price": 149.99, "stock_qty": 10},
    {"name": "Camping Tent - 4 Person", "category": "Sports & Outdoors", "description": "Weatherproof 4-person dome tent, easy setup.", "price": 89.99, "stock_qty": 14},
    {"name": "Insulated Hiking Backpack", "category": "Sports & Outdoors", "description": "30L hiking backpack with hydration reservoir compatibility.", "price": 54.99, "stock_qty": 24},
    {"name": "Resistance Bands Set", "category": "Sports & Outdoors", "description": "5-piece resistance band set with door anchor.", "price": 17.99, "stock_qty": 80},
    {"name": "Running Shoes - Trail", "category": "Sports & Outdoors", "description": "Lightweight trail running shoes with grip sole.", "price": 64.99, "stock_qty": 32},
    {"name": "Foldable Camping Chair", "category": "Sports & Outdoors", "description": "Compact folding chair with cup holder and carry bag.", "price": 27.99, "stock_qty": 38},
    # Books
    {"name": "The Art of Clean Code", "category": "Books", "description": "A practical guide to writing maintainable software.", "price": 34.99, "stock_qty": 20},
    {"name": "Mindful Cooking", "category": "Books", "description": "A cookbook focused on simple, seasonal recipes.", "price": 24.99, "stock_qty": 25},
    {"name": "The History of Space Exploration", "category": "Books", "description": "An illustrated history of humanity's journey to space.", "price": 29.99, "stock_qty": 18},
    {"name": "Personal Finance Basics", "category": "Books", "description": "A beginner's guide to budgeting, saving, and investing.", "price": 19.99, "stock_qty": 30},
    {"name": "Learning to Garden", "category": "Books", "description": "A practical handbook for first-time gardeners.", "price": 21.99, "stock_qty": 22},
    # Clothing
    {"name": "Merino Wool Sweater", "category": "Clothing", "description": "Soft merino wool crewneck sweater, machine washable.", "price": 59.99, "stock_qty": 26},
    {"name": "Waterproof Rain Jacket", "category": "Clothing", "description": "Lightweight waterproof jacket with packable hood.", "price": 74.99, "stock_qty": 20},
    {"name": "Classic Denim Jacket", "category": "Clothing", "description": "Timeless denim jacket, regular fit.", "price": 49.99, "stock_qty": 33},
    {"name": "Athletic Performance Socks (3-Pack)", "category": "Clothing", "description": "Moisture-wicking athletic socks, 3 pairs.", "price": 14.99, "stock_qty": 70},
    {"name": "Fleece-Lined Beanie", "category": "Clothing", "description": "Warm knit beanie with soft fleece lining.", "price": 12.99, "stock_qty": 85},
]

CUSTOMERS = [
    {"email": "alice.nguyen@example.com", "name": "Alice Nguyen"},
    {"email": "brian.tran@example.com", "name": "Brian Tran"},
    {"email": "cathy.pham@example.com", "name": "Cathy Pham"},
    {"email": "david.le@example.com", "name": "David Le"},
    {"email": "emma.vu@example.com", "name": "Emma Vu"},
    {"email": "frank.hoang@example.com", "name": "Frank Hoang"},
    {"email": "grace.dang@example.com", "name": "Grace Dang"},
    {"email": "henry.bui@example.com", "name": "Henry Bui"},
]

FAQS = [
    {"question": "What is your return policy?", "answer": "We accept returns within 30 days of delivery for a full refund, as long as the item is unused and in its original packaging."},
    {"question": "How long does shipping take?", "answer": "Standard shipping takes 3-7 business days. Orders are marked 'processing' for the first 24 hours, then 'shipped' until delivery."},
    {"question": "Do you offer free shipping?", "answer": "Yes, we offer free standard shipping on all orders over $50. Orders under $50 have a flat $5.99 shipping fee."},
    {"question": "Can I change or cancel my order after placing it?", "answer": "Orders can be modified or cancelled within 1 hour of placing them, before they move to 'processing'. Contact support immediately if you need a change."},
    {"question": "What payment methods do you accept?", "answer": "We accept all major credit cards, debit cards, and PayPal."},
    {"question": "How do I track my order?", "answer": "You can track your order status (processing, shipped, or delivered) directly through our chat assistant by providing your order number."},
    {"question": "What is your warranty policy?", "answer": "Electronics come with a 1-year manufacturer warranty covering defects. Contact support with your order number to start a warranty claim."},
    {"question": "Do you ship internationally?", "answer": "Currently we only ship within the country. International shipping is on our roadmap for the future."},
    {"question": "How do I create a return or exchange?", "answer": "Log into your account, go to Order History, select the item, and choose 'Start a Return'. You'll receive a prepaid shipping label."},
    {"question": "What if I received a damaged or defective item?", "answer": "We're sorry for the inconvenience -- contact support with your order number and photos of the damage, and we'll send a free replacement or refund."},
    {"question": "Do you price match?", "answer": "We price match identical items from major retailers within 14 days of purchase. Contact support with a link to the lower price."},
    {"question": "How can I check if an item is in stock?", "answer": "Product pages show real-time stock availability, or you can ask our assistant to check stock for a specific product."},
    {"question": "Can I use multiple discount codes on one order?", "answer": "Only one discount code can be applied per order."},
    {"question": "How do I update my shipping address?", "answer": "You can update your shipping address in your account settings before placing an order. Addresses on already-placed orders cannot be changed after they ship."},
    {"question": "What should I do if my package says delivered but I haven't received it?", "answer": "Please wait 24 hours as carriers sometimes mark packages early. If it still hasn't arrived, contact support and we'll investigate with the carrier."},
    {"question": "Do you offer gift wrapping?", "answer": "Yes, gift wrapping is available at checkout for a small additional fee."},
    {"question": "How do loyalty points work?", "answer": "You earn 1 point per $1 spent. 100 points can be redeemed for a $5 discount on a future order."},
    {"question": "Can I return a gift I received?", "answer": "Yes, gift returns are accepted within 30 days with the order number or gift receipt, and refunds are issued as store credit."},
]


def seed_products() -> list[dict]:
    result = client.table("products").insert(PRODUCTS).execute()
    print(f"Inserted {len(result.data)} products")
    return result.data


def seed_customers() -> list[dict]:
    result = client.table("customers").insert(CUSTOMERS).execute()
    print(f"Inserted {len(result.data)} customers")
    return result.data


def _status_for_age(created_at: datetime) -> str:
    age = datetime.now(timezone.utc) - created_at
    if age < timedelta(days=1):
        return "processing"
    if age < timedelta(days=7):
        return "shipped"
    return "delivered"


def seed_orders_and_items(products: list[dict], customers: list[dict]) -> None:
    # bucket: <1 day (processing), 1-7 days (shipped), >7 days (delivered).
    age_buckets_days = [0, 0, 2, 4, 5, 9, 14, 20, 0, 3, 6, 11, 1, 8, 17, 0, 4, 15]

    orders_to_insert = []
    order_meta = []  # parallel list: (created_at, customer_id, line_items)
    for age_days in age_buckets_days:
        created_at = datetime.now(timezone.utc) - timedelta(
            days=age_days, hours=random.randint(0, 23)
        )
        customer = random.choice(customers)
        line_items = []
        for product in random.sample(products, k=random.randint(1, 4)):
            quantity = random.randint(1, 3)
            line_items.append(
                {
                    "product_id": product["id"],
                    "quantity": quantity,
                    "unit_price": product["price"],
                }
            )
        total = round(
            sum(item["unit_price"] * item["quantity"] for item in line_items), 2
        )

        orders_to_insert.append(
            {
                "customer_id": customer["id"],
                "status": _status_for_age(created_at),
                "created_at": created_at.isoformat(),
                "total": total,
            }
        )
        order_meta.append(line_items)

    orders_result = client.table("orders").insert(orders_to_insert).execute()
    print(f"Inserted {len(orders_result.data)} orders")

    order_items_to_insert = []
    for order_row, line_items in zip(orders_result.data, order_meta):
        for item in line_items:
            order_items_to_insert.append({"order_id": order_row["id"], **item})

    items_result = client.table("order_items").insert(order_items_to_insert).execute()
    print(f"Inserted {len(items_result.data)} order_items")


def seed_faqs() -> None:
    embeddings = init_embeddings("openai:text-embedding-3-small")
    documents = [
        Document(
            page_content=f"Q: {faq['question']}\nA: {faq['answer']}",
            metadata={"question": faq["question"], "answer": faq["answer"]},
        )
        for faq in FAQS
    ]
    SupabaseVectorStore.from_documents(
        documents,
        embeddings,
        client=client,
        table_name="documents",
        query_name="match_documents",
    )
    print(f"Inserted {len(documents)} FAQ documents")


if __name__ == "__main__":
    products = seed_products()
    customers = seed_customers()
    seed_orders_and_items(products, customers)
    seed_faqs()
