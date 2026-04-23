def get_batch_stats(requests: list[BatchRequest]) -> dict:
    """
    Compute statistics about a batch.

    Args:
        requests: List of BatchRequest

    Returns:
        Dict with batch statistics
    """
    by_type = split_by_type(requests)

    return {
        "total_requests": len(requests),
        "num_decode": len(by_type["decode"]),
        "num_prefill": len(by_type["prefill"]),
        "num_extend": len(by_type["extend"]),
        "total_tokens": sum(r.q_len for r in requests),
        "total_kv_cache": sum(r.kv_len for r in requests),
        "max_q_len": max((r.q_len for r in requests), default=0),
        "max_kv_len": max((r.kv_len for r in requests), default=0),
        "avg_q_len": sum(r.q_len for r in requests) / len(requests) if requests else 0,
        "avg_kv_len": (
            sum(r.kv_len for r in requests) / len(requests) if requests else 0
        ),
    }