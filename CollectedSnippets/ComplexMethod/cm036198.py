def extract_acceptance_metrics(metrics, num_spec_tokens: int) -> dict:
    num_drafts = 0
    num_accepted_tokens = 0
    acceptance_counts = [0] * num_spec_tokens

    for metric in metrics:
        if metric.name == "vllm:spec_decode_num_drafts":
            assert isinstance(metric, Counter)
            num_drafts += metric.value
        elif metric.name == "vllm:spec_decode_num_accepted_tokens":
            assert isinstance(metric, Counter)
            num_accepted_tokens += metric.value
        elif metric.name == "vllm:spec_decode_num_accepted_tokens_per_pos":
            assert isinstance(metric, Vector)
            for pos in range(min(len(metric.values), num_spec_tokens)):
                acceptance_counts[pos] += metric.values[pos]

    # Calculate mean acceptance length
    # Formula: 1 + (accepted_tokens / num_drafts)
    acceptance_length = 1 + (num_accepted_tokens / num_drafts) if num_drafts > 0 else 1

    # Calculate per-position acceptance lengths (contribution to total)
    # Each position contributes: accepted_at_pos / num_drafts
    acceptance_lengths_per_pos = [
        count / num_drafts if num_drafts > 0 else 0.0 for count in acceptance_counts
    ]

    return {
        "acceptance_length": acceptance_length,
        "acceptance_lengths_per_pos": acceptance_lengths_per_pos,
        "num_drafts": num_drafts,
        "num_accepted_tokens": num_accepted_tokens,
    }