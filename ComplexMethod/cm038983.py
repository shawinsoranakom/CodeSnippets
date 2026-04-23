def get_batch_type(batch_spec: str, spec_decode_threshold: int = 8) -> str:
    """
    Classify a batch spec into a type string.

    Args:
        batch_spec: Batch specification string (e.g., "q2k", "8q1s1k", "2q2k_8q1s1k")
        spec_decode_threshold: Max q_len to be considered spec-decode vs extend

    Returns:
        Type string: "prefill", "decode", "spec-decode", "extend", or "mixed (types...)"
    """
    requests = parse_batch_spec(batch_spec)

    # Classify each request
    types_present = set()
    for req in requests:
        if req.is_decode:
            types_present.add("decode")
        elif req.is_prefill:
            types_present.add("prefill")
        elif req.is_extend:
            # Distinguish spec-decode (small q_len) from extend (chunked prefill)
            if req.q_len <= spec_decode_threshold:
                types_present.add("spec-decode")
            else:
                types_present.add("extend")

    if len(types_present) == 1:
        return types_present.pop()
    elif len(types_present) > 1:
        # Sort for consistent output
        sorted_types = sorted(types_present)
        return f"mixed ({'+'.join(sorted_types)})"
    else:
        return "unknown"