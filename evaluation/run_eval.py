import asyncio
from uuid import uuid4

from src.agent.graph import graph
from evaluation.datasets import (
    TEST_USER_EMAIL,
    client,
    accuracy_dataset_name,
    tool_usage_dataset_name,
)
from evaluation.evaluators import final_answer_correct, used_expected_tools

async def run_graph(input: dict) -> dict:
    """Run the graph for a single question and return the final response.
    """
    result = graph.invoke(
        {
            "messages": [
                {"role": "user", "content": input["question"]},
            ]
        },
        config={
            "configurable": {
                "thread_id": f"eval-accuracy-{uuid4()}",
                "user_email": TEST_USER_EMAIL,
            }
        },
    )
    return {"response": result["messages"][-1].content}

accuracy_results = asyncio.run(
    client.aevaluate(
        run_graph,
        data=accuracy_dataset_name,
        evaluators=[final_answer_correct],
        experiment_prefix="customer-service-accuracy",
        max_concurrency=4,
    )
)

accuracy_runs = list(
    client.list_runs(project_name=accuracy_results.experiment_name, is_root=True)
)
accuracy_feedback = list(
    client.list_feedback(run_ids=[r.id for r in accuracy_runs])
)
accuracy_scores = [f.score for f in accuracy_feedback]
print(f"Response accuracy: {len(accuracy_scores)} scores -> {accuracy_scores}")

# tool usage efficiency
async def run_graph_with_trajectory(inputs: dict) -> dict:
    """Run the graph for a single question and return which tools it called."""
    result = graph.invoke(
        {
            "messages": [
                {"role": "user", "content": inputs["question"]},
            ]
        },
        config={
            "configurable": {
                "thread_id": f"eval-efficiency-{uuid4()}",
                "user_email": TEST_USER_EMAIL,
            }
        },
    )
    tools_called = [
        tool_call["name"]
        for message in result["messages"]
        for tool_call in (getattr(message, "tool_calls", None) or [])
    ]
    return {"tools_called": tools_called}

tool_usage_results = asyncio.run(
    client.aevaluate(
        run_graph_with_trajectory,
        data=tool_usage_dataset_name,
        evaluators=[used_expected_tools],
        experiment_prefix="customer-service-efficiency",
        max_concurrency=4,
    )
)
