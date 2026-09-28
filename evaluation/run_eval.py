import asyncio
from uuid import uuid4

from src.agent.graph import graph
from evaluation.datasets import TEST_USER_EMAIL, client, accuracy_dataset_name
from evaluation.evaluators import final_answer_correct

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
