def format_batch_spec(requests: list[BatchRequest]) -> str:
    """
    Format list of BatchRequest into human-readable string.

    Groups requests by type and provides counts and sizes.

    Args:
        requests: List of BatchRequest objects

    Returns:
        Formatted string describing the batch
    """
    kinds = {
        "prefill": [],
        "extend": [],
        "decode": [],
    }

    for req in requests:
        tup = (req.q_len, req.kv_len)
        if req.is_prefill:
            kinds["prefill"].append(tup)
        elif req.is_extend:
            kinds["extend"].append(tup)
        elif req.is_decode:
            kinds["decode"].append(tup)

    parts = []
    for kind in ["prefill", "extend", "decode"]:
        lst = kinds[kind]
        if not lst:
            continue

        cnt_total = len(lst)
        ctr = Counter(lst)
        inner = []

        for (q, kv), cnt in ctr.items():
            if kind == "prefill":
                size = f"{q // 1024}k" if q % 1024 == 0 else str(q)
                inner.append(f"{cnt}x{size}")
            elif kind == "decode":
                size = f"{kv // 1024}k" if kv % 1024 == 0 else str(kv)
                inner.append(f"{cnt}x{size}")
            else:  # extend
                qstr = f"{q // 1024}k" if q % 1024 == 0 else str(q)
                kstr = f"{kv // 1024}k" if kv % 1024 == 0 else str(kv)
                inner.append(f"{cnt}xq{qstr}kv{kstr}")

        parts.append(f"{cnt_total} {kind} ({', '.join(inner)})")

    return ", ".join(parts)