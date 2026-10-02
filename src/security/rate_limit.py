import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from supabase import create_client

_ = load_dotenv()

client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])

MAX_MESSAGES = int(os.environ.get("RATE_LIMIT_MAX_MESSAGES", "20"))
WINDOW_MINUTES = int(os.environ.get("RATE_LIMIT_WINDOW_MINUTES", "60"))
EXEMPT_EMAILS = {
    email.strip()
    for email in os.environ.get("RATE_LIMIT_EXEMPT_EMAILS", "").split(",")
    if email.strip()
}


def check_and_increment(email: str) -> bool:
    """Return True if this message is allowed, False if the customer is over
    their rate limit. Increments the stored counter as a side effect when
    the message is allowed. Exempt emails always return True and never touch
    the counter.
    """
    if email in EXEMPT_EMAILS:
        return True

    now = datetime.now(timezone.utc)
    result = (
        client.table("rate_limits").select("*").eq("customer_email", email).execute()
    )

    if not result.data:
        client.table("rate_limits").insert(
            {
                "customer_email": email,
                "window_start": now.isoformat(),
                "message_count": 1,
            }
        ).execute()
        return True

    row = result.data[0]
    window_start = datetime.fromisoformat(row["window_start"])
    if now - window_start > timedelta(minutes=WINDOW_MINUTES):
        client.table("rate_limits").update(
            {"window_start": now.isoformat(), "message_count": 1}
        ).eq("customer_email", email).execute()
        return True

    if row["message_count"] >= MAX_MESSAGES:
        return False

    client.table("rate_limits").update(
        {"message_count": row["message_count"] + 1}
    ).eq("customer_email", email).execute()
    return True
