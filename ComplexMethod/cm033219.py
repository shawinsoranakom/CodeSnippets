def _collect_canvas_types(canvas_type: Any, canvas_types: Any) -> list[str]:
    categories: list[str] = []

    if isinstance(canvas_type, str):
        category = canvas_type.strip()
        if category:
            categories.append(category)

    iterable_types: list[Any]
    if isinstance(canvas_types, list):
        iterable_types = canvas_types
    elif canvas_types is None:
        iterable_types = []
    else:
        iterable_types = [canvas_types]

    for item in iterable_types:
        if not isinstance(item, str):
            continue
        category = item.strip()
        if not category:
            continue
        categories.append(category)

    deduplicated: list[str] = []
    seen: set[str] = set()
    for category in categories:
        if category in seen:
            continue
        seen.add(category)
        deduplicated.append(category)

    return deduplicated