from langsmith import Client

TEST_USER_EMAIL = "nguyenvanducnhat@gmail.com"

client = Client()

accuracy_examples = [
    {
        "inputs": {
            "question": "What is the price of the Air Fryer 5.8-Quart?"
        },
        "outputs": {"response": "The Air Fryer 5.8-Quart is $79.99."},
    },
    {
        "inputs": {"question": "What is the status of order 7?"},
        "outputs": {"response": "Order 7 has been delivered."},
    },
    {
        "inputs": {"question": "What is your return policy?"},
        "outputs": {
            "response": "Returns are accepted within 30 days of delivery for a full refund, provided the item is unused and in its original packaging."
        },
    },
    {
        "inputs": {
            "question": "How many Wireless Bluetooth Headphones do you have in stock, and what's the price?"
        },
        "outputs": {
            "response": "There are 42 Wireless Bluetooth Headphones in stock, priced at $89.99."
        },
    },
    {
        "inputs": {"question": "What was the total for order 12?"},
        "outputs": {"response": "Order 12 has a total of $289.94 and has been delivered."},
    },
    {
        "inputs": {"question": "What orders have I placed?"},
        "outputs": {
            "response": "You have placed 3 orders: order 4 ($119.95, shipped), order 7 ($259.94, delivered), and order 12 ($289.94, delivered)."
        },
    },
    {
        "inputs": {"question": "Can I cancel order 7?"},
        "outputs": {
            "response": "No, order 7 can't be cancelled -- cancellations are only allowed within 1 hour of placing an order, and order 7 was placed weeks ago."
        },
    },
    {
        "inputs": {
            "question": "If I want to cancel an order, when am I able to do that?"
        },
        "outputs": {
            "response": "You can cancel or modify an order within 1 hour of placing it, before it moves to processing. After that, you'd need to contact support."
        },
    },
    {
        "inputs": {
            "question": "What do you have in the Home & Kitchen category under $50?"
        },
        "outputs": {
            "response": "Home & Kitchen items under $50 include the Stainless Steel Water Bottle ($24.99), Programmable Coffee Maker ($44.99), Cast Iron Skillet 10-inch ($32.99), Bamboo Cutting Board Set ($19.99), and Memory Foam Pillow ($29.99)."
        },
    },
    {
        "inputs": {"question": "Can you recommend a good coffee maker?"},
        "outputs": {
            "response": "The Programmable Coffee Maker is a good choice -- a 12-cup programmable coffee maker with auto shut-off, priced at $44.99, with 22 in stock."
        },
    },
]

accuracy_dataset_name = "Customer Service Agent: Response Accuracy"

if not client.has_dataset(dataset_name=accuracy_dataset_name):
    accuracy_dataset = client.create_dataset(accuracy_dataset_name)
    client.create_examples(
        dataset_id=accuracy_dataset.id, examples=accuracy_examples
    )

tool_usage_examples = [
    {
        "inputs": {
            "question": "What's the price of the Air Fryer and how does it compare to competitors?"
        },
        "outputs": {"expected_tools": ["price_comparison_tool"]},
    },
    {
        "inputs": {"question": "What's the status of order 7?"},
        "outputs": {"expected_tools": ["shipping_tracker_tool"]},
    },
    {
        "inputs": {"question": "What is your return policy?"},
        "outputs": {"expected_tools": ["faq_lookup_tool"]},
    },
    {
        "inputs": {
            "question": "How many products do you have in Electronics?"
        },
        "outputs": {"expected_tools": ["sql_db_query"]},
    },
    {
        "inputs": {"question": "What's the weather in Da Nang?"},
        "outputs": {"expected_tools": []},
    },
    {
        "inputs": {"question": "What orders have I placed?"},
        "outputs": {"expected_tools": ["sql_db_query"]},
    },
    {
        "inputs": {"question": "Can I cancel order 7?"},
        "outputs": {"expected_tools": ["sql_db_query"]},
    },
    {
        "inputs": {
            "question": "If I want to cancel an order, when am I able to do that?"
        },
        "outputs": {"expected_tools": ["faq_lookup_tool"]},
    },
    {
        "inputs": {
            "question": "What do you have in the Home & Kitchen category under $50?"
        },
        "outputs": {"expected_tools": ["sql_db_query"]},
    },
    {
        "inputs": {"question": "Can you recommend a good coffee maker?"},
        "outputs": {"expected_tools": ["sql_db_query"]},
    },
]

tool_usage_dataset_name = "Customer Service Agent: Tool Usage Efficiency"

if not client.has_dataset(dataset_name=tool_usage_dataset_name):
    tool_usage_dataset = client.create_dataset(tool_usage_dataset_name)
    client.create_examples(
        dataset_id=tool_usage_dataset.id, examples=tool_usage_examples
    )

flow_examples = [
    {
        "inputs": {
            "messages": [
                "What's the price of the Air Fryer 5.8-Quart?",
                "How does it compare to competitors?",
            ]
        },
        "outputs": {
            "response": "The Air Fryer 5.8-Quart is $79.99, which is competitively priced compared to similar air fryers from other brands."
        },
    },
    {
        "inputs": {
            "messages": [
                "What's the status of order 7?",
                "When will it arrive?",
            ]
        },
        "outputs": {
            "response": "Order 7 has already been delivered, so there's no further delivery estimate needed."
        },
    },
    {
        "inputs": {
            "messages": [
                "What is your return policy?",
                "What's the weather like today?",
                "Sorry, back to my question -- how many days do I have to return an item?",
            ]
        },
        "outputs": {
            "response": "You have 30 days from delivery to return an item for a full refund, as long as it's unused and in its original packaging."
        },
    },
    {
        "inputs": {
            "messages": [
                "How many Wireless Bluetooth Headphones do you have in stock?",
                "And what's the price?",
            ]
        },
        "outputs": {
            "response": "There are 42 Wireless Bluetooth Headphones in stock, priced at $89.99."
        },
    },
    {
        "inputs": {
            "messages": [
                "What was the total for order 12?",
                "Has it been delivered yet?",
            ]
        },
        "outputs": {
            "response": "Order 12 had a total of $289.94, and yes, it has already been delivered."
        },
    },
]

flow_dataset_name = "Customer Service Agent: Conversation Flow"

if not client.has_dataset(dataset_name=flow_dataset_name):
    flow_dataset = client.create_dataset(flow_dataset_name)
    client.create_examples(dataset_id=flow_dataset.id, examples=flow_examples)

error_examples = [
    {
        "inputs": {"question": "What is the status of order abc123?"},
        "outputs": {"should_be_graceful": True},
    },
    {
        "inputs": {"question": "Do you sell a Quantum Levitation Skateboard?"},
        "outputs": {"should_be_graceful": True},
    },
    {
        "inputs": {"question": "What is the status of order 2?"},
        "outputs": {"should_be_graceful": True},
    }, 
    {
        "inputs": {"question": "What's the weather in Da Nang?"},
        "outputs": {"should_be_graceful": True},
    },
    {
        "inputs": {"question": "My order arrived damaged, I'm really frustrated."},
        "outputs": {"should_be_graceful": True},
    },
]

error_dataset_name = "Customer Service Agent: Error Handling"

if not client.has_dataset(dataset_name=error_dataset_name):
    error_dataset = client.create_dataset(error_dataset_name)
    client.create_examples(dataset_id=error_dataset.id, examples=error_examples)
