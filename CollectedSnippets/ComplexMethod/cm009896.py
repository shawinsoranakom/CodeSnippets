def _low_confidence_spans(
    tokens: Sequence[str],
    log_probs: Sequence[float],
    min_prob: float,
    min_token_gap: int,
    num_pad_tokens: int,
) -> list[str]:
    try:
        import numpy as np

        _low_idx = np.where(np.exp(log_probs) < min_prob)[0]
    except ImportError:
        logger.warning(
            "NumPy not found in the current Python environment. FlareChain will use a "
            "pure Python implementation for internal calculations, which may "
            "significantly impact performance, especially for large datasets. For "
            "optimal speed and efficiency, consider installing NumPy: pip install "
            "numpy",
        )
        import math

        _low_idx = [  # type: ignore[assignment]
            idx
            for idx, log_prob in enumerate(log_probs)
            if math.exp(log_prob) < min_prob
        ]
    low_idx = [i for i in _low_idx if re.search(r"\w", tokens[i])]
    if len(low_idx) == 0:
        return []
    spans = [[low_idx[0], low_idx[0] + num_pad_tokens + 1]]
    for i, idx in enumerate(low_idx[1:]):
        end = idx + num_pad_tokens + 1
        if idx - low_idx[i] < min_token_gap:
            spans[-1][1] = end
        else:
            spans.append([idx, end])
    return ["".join(tokens[start:end]) for start, end in spans]