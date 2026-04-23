def calculate_metrics_for_embeddings(
    outputs: list[RequestFuncOutput],
    dur_s: float,
    selected_percentiles: list[float],
) -> EmbedBenchmarkMetrics:
    """Calculate the metrics for the embedding requests.

    Args:
        outputs: The outputs of the requests.
        dur_s: The duration of the benchmark.
        selected_percentiles: The percentiles to select.

    Returns:
        The calculated benchmark metrics.
    """
    total_input = 0
    completed = 0
    failed = 0
    e2els: list[float] = []
    for i in range(len(outputs)):
        if outputs[i].success:
            e2els.append(outputs[i].latency)
            completed += 1
            total_input += outputs[i].prompt_len
        else:
            failed += 1

    if completed == 0:
        warnings.warn(
            "All requests failed. This is likely due to a misconfiguration "
            "on the benchmark arguments.",
            stacklevel=2,
        )
    metrics = EmbedBenchmarkMetrics(
        completed=completed,
        failed=failed,
        total_input=total_input,
        request_throughput=completed / dur_s,
        total_token_throughput=total_input / dur_s,
        mean_e2el_ms=np.mean(e2els or 0) * 1000,
        std_e2el_ms=np.std(e2els or 0) * 1000,
        median_e2el_ms=np.median(e2els or 0) * 1000,
        percentiles_e2el_ms=[
            (p, np.percentile(e2els or 0, p) * 1000) for p in selected_percentiles
        ],
    )
    return metrics