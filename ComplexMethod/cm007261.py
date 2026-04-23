def search_registry(
    registry: dict[str, dict],
    query: str | None = None,
    category: str | None = None,
    output_type: str | None = None,
) -> list[dict[str, Any]]:
    """Search the registry by name/category/output_type. Pure function."""
    results = []
    for name, tmpl in sorted(registry.items()):
        cat = tmpl.get("category", "")
        if category and cat.lower() != category.lower():
            continue
        if query and query.lower() not in name.lower() and query.lower() not in cat.lower():
            continue
        if output_type:
            all_types = [t for o in tmpl.get("outputs", []) for t in o.get("types", [])]
            if output_type not in all_types:
                continue
        results.append(
            {
                "type": name,
                "category": cat,
                "display_name": tmpl.get("display_name", name),
                "description": tmpl.get("description", ""),
            }
        )
    return results