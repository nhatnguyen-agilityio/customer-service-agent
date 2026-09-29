import asyncio
from uuid import uuid4

from src.agent.graph import graph
from evaluation.datasets import (
    TEST_USER_EMAIL,
    client,
    accuracy_dataset_name,
    tool_usage_dataset_name,
    flow_dataset_name,
    error_dataset_name,
)
from evaluation.evaluators import (
    final_answer_correct,
    used_expected_tools,
    conversation_coherent,
    is_graceful_response,
)

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

async def run_conversation(inputs: dict) -> dict:
    """Replay a multi-turn conversation one turn at a time on the same fresh
    thread, so each turn relies on the checkpointer's persisted memory
    """
    config = {
        "configurable": {
            "thread_id": f"eval-flow-{uuid4()}",
            "user_email": TEST_USER_EMAIL,
        }
    }
    result = None
    for turn in inputs["messages"]:
        result = graph.invoke(
            {"messages": [{"role": "user", "content": turn}]},
            config=config,
        )
    return {"response": result["messages"][-1].content}


if __name__ == "__main__":
    accuracy_results = asyncio.run(
        client.aevaluate(
            run_graph,
            data=accuracy_dataset_name,
            evaluators=[final_answer_correct],
            experiment_prefix="customer-service-accuracy",
            max_concurrency=4,
        )
    )

    tool_usage_results = asyncio.run(
        client.aevaluate(
            run_graph_with_trajectory,
            data=tool_usage_dataset_name,
            evaluators=[used_expected_tools],
            experiment_prefix="customer-service-efficiency",
            max_concurrency=4,
        )
    )

    run_conversation_results = asyncio.run(
        client.aevaluate(
            run_conversation,
            data=flow_dataset_name,
            evaluators=[conversation_coherent],
            experiment_prefix="customer-service-conversation-flow",
            max_concurrency=4,
        )
    )

    # error handling evaluation
    error_results = asyncio.run(
        client.aevaluate(
            run_graph,
            data=error_dataset_name,
            evaluators=[is_graceful_response],
            experiment_prefix="customer-service-error-handling",
            max_concurrency=4,
        )
    )

    experiments = [
        ("Response accuracy", accuracy_results),
        ("Tool usage efficiency", tool_usage_results),
        ("Conversation flow", run_conversation_results),
        ("Error handling", error_results),
    ]

    for name, results in experiments:
        runs = list(
            client.list_runs(project_name=results.experiment_name, is_root=True)
        )
        feedback = list(client.list_feedback(run_ids=[r.id for r in runs]))
        scores = [f.score for f in feedback]
        pass_rate = sum(scores) / len(scores) if scores else 0.0
        print(f"{name}: {len(scores)} scores -> {scores} (pass rate: {pass_rate:.0%})")
