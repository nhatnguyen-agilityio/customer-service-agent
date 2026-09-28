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
]

tool_usage_dataset_name = "Customer Service Agent: Tool Usage Efficiency"

if not client.has_dataset(dataset_name=tool_usage_dataset_name):
    tool_usage_dataset = client.create_dataset(tool_usage_dataset_name)
    client.create_examples(
        dataset_id=tool_usage_dataset.id, examples=tool_usage_examples
    ) 
