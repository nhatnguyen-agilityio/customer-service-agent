from dotenv import load_dotenv

load_dotenv()

from evaluation.datasets import client

# LangSmith already records latency/tokens/cost on every traced run -- this
# just reads that data back via the SDK, no new instrumentation needed.
CATEGORY_PREFIXES = [
    ("Response accuracy", "customer-service-accuracy"),
    ("Tool usage efficiency", "customer-service-efficiency"),
    ("Conversation flow", "customer-service-conversation-flow"),
    ("Error handling", "customer-service-error-handling"),
]


def latest_experiment(name_contains: str):
    projects = list(client.list_projects(name_contains=name_contains))
    if not projects:
        return None
    projects.sort(key=lambda p: p.start_time or p.created_at, reverse=True)
    return projects[0]


def metrics_for_run(r):
    latency = None
    if r.start_time and r.end_time:
        latency = (r.end_time - r.start_time).total_seconds()
    return {
        "latency": latency,
        "total_tokens": r.total_tokens,
        "prompt_tokens": r.prompt_tokens,
        "completion_tokens": r.completion_tokens,
        "total_cost": r.total_cost,
    }


def average(values):
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None


def fmt(value, digits=4):
    return f"{value:.{digits}f}" if value is not None else "N/A"


if __name__ == "__main__":
    all_metrics = []

    for label, prefix in CATEGORY_PREFIXES:
        experiment = latest_experiment(prefix)
        if experiment is None:
            print(f"{label}: no experiment found (matching '{prefix}')")
            continue

        runs = list(client.list_runs(project_name=experiment.name, is_root=True))
        run_metrics = [metrics_for_run(r) for r in runs]
        all_metrics.extend(run_metrics)

        print(f"{label} ({experiment.name}, {len(runs)} runs)")
        print(f"  avg latency:           {fmt(average([m['latency'] for m in run_metrics]), 2)} s")
        print(f"  avg total tokens:      {fmt(average([m['total_tokens'] for m in run_metrics]), 0)}")
        print(f"  avg prompt tokens:     {fmt(average([m['prompt_tokens'] for m in run_metrics]), 0)}")
        print(f"  avg completion tokens: {fmt(average([m['completion_tokens'] for m in run_metrics]), 0)}")
        print(f"  avg cost:              ${fmt(average([m['total_cost'] for m in run_metrics]), 6)}")
        print()

    if all_metrics:
        print(f"Overall across all {len(all_metrics)} runs")
        print(f"  avg latency:           {fmt(average([m['latency'] for m in all_metrics]), 2)} s")
        print(f"  avg total tokens:      {fmt(average([m['total_tokens'] for m in all_metrics]), 0)}")
        print(f"  total cost:            ${fmt(sum(m['total_cost'] for m in all_metrics if m['total_cost'] is not None), 4)}")
