def extract_entries(
    categories: list[ParsedSection],
    groups: list[ParsedGroup],
) -> list[dict]:
    """Flatten categories into individual library entries for table display.

    Entries appearing in multiple categories are merged into a single entry
    with lists of categories and groups.
    """
    cat_to_group = {cat["name"]: group["name"] for group in groups for cat in group["categories"]}

    seen: dict[tuple[str, str], dict[str, Any]] = {}  # (url, name) -> entry
    entries: list[dict[str, Any]] = []
    for cat in categories:
        group_name = cat_to_group.get(cat["name"], "Other")
        for entry in cat["entries"]:
            key = (entry["url"], entry["name"])
            existing: dict[str, Any] | None = seen.get(key)
            if existing is None:
                existing = {
                    "name": entry["name"],
                    "url": entry["url"],
                    "description": entry["description"],
                    "categories": [],
                    "groups": [],
                    "subcategories": [],
                    "stars": None,
                    "owner": None,
                    "last_commit_at": None,
                    "source_type": detect_source_type(entry["url"]),
                    "also_see": entry["also_see"],
                }
                seen[key] = existing
                entries.append(existing)
            if cat["name"] not in existing["categories"]:
                existing["categories"].append(cat["name"])
            if group_name not in existing["groups"]:
                existing["groups"].append(group_name)
            subcat = entry["subcategory"]
            if subcat:
                scoped = f"{cat['name']} > {subcat}"
                if not any(s["value"] == scoped for s in existing["subcategories"]):
                    existing["subcategories"].append({"name": subcat, "value": scoped})
    return entries