def select_visible_gpu_rows(
    gpu_rows: Iterable[tuple[str, str, str]],
    visible_devices: list[str] | None,
) -> list[tuple[str, str, str]]:
    rows = list(gpu_rows)
    if visible_devices is None:
        return rows
    if not visible_devices:
        return []

    by_index = {index: (index, uuid, cap) for index, uuid, cap in rows}
    by_uuid = {uuid.lower(): (index, uuid, cap) for index, uuid, cap in rows}
    selected: list[tuple[str, str, str]] = []
    seen_indices: set[str] = set()
    for token in visible_devices:
        row = by_index.get(token)
        if row is None:
            normalized_token = token.lower()
            row = by_uuid.get(normalized_token)
            if row is None and normalized_token.startswith("gpu-"):
                row = by_uuid.get(normalized_token)
            if row is None and not normalized_token.startswith("gpu-"):
                row = by_uuid.get("gpu-" + normalized_token)
        if row is None:
            continue
        index = row[0]
        if index in seen_indices:
            continue
        seen_indices.add(index)
        selected.append(row)
    return selected