def _round_robin_preview(
    rows: list[dict[str, str]],
    preview_size: int,
) -> list[dict[str, str]]:
    """Pick preview rows round-robin across source files so every file is represented."""
    if not rows or preview_size <= 0:
        return []

    # Group rows by source_file, preserving order of first appearance
    from collections import OrderedDict

    grouped: OrderedDict[str, list[dict[str, str]]] = OrderedDict()
    for row in rows:
        key = row.get("source_file", "")
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(row)

    result: list[dict[str, str]] = []
    iterators = [iter(chunks) for chunks in grouped.values()]
    while len(result) < preview_size and iterators:
        exhausted: list[int] = []
        for i, it in enumerate(iterators):
            if len(result) >= preview_size:
                break
            val = next(it, None)
            if val is not None:
                result.append(val)
            else:
                exhausted.append(i)
        for i in reversed(exhausted):
            iterators.pop(i)

    return result