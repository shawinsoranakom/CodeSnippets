def aggregate_by_field(messages: list | None, field_name: str) -> list[tuple[str, int]]:
    """Aggregate message documents by a field; returns [(value, count), ...].

    Handles pre-aggregated rows (dicts with "value" and "count") and
    per-doc field values (str or list of str).
    """
    if not messages:
        return []

    counts: dict[str, int] = {}
    result: list[tuple[str, int]] = []

    for doc in messages:
        if "value" in doc and "count" in doc:
            result.append((doc["value"], doc["count"]))
            continue

        if field_name not in doc:
            continue

        v = doc[field_name]
        if isinstance(v, list):
            for vv in v:
                if isinstance(vv, str):
                    key = vv.strip()
                    if key:
                        counts[key] = counts.get(key, 0) + 1
        elif isinstance(v, str):
            key = v.strip()
            if key:
                counts[key] = counts.get(key, 0) + 1

    if counts:
        for k, v in counts.items():
            result.append((k, v))

    return result