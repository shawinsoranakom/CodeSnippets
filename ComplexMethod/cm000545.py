def _disambiguate_tool_names(tools: list[dict[str, Any]]) -> None:
    """Ensure all tool names are unique (Anthropic API requires this).

    When multiple nodes use the same block type, they get the same tool name.
    This appends _1, _2, etc. and enriches descriptions with hardcoded defaults
    so the LLM can distinguish them. Mutates the list in place.

    Malformed tools (missing ``function`` or ``function.name``) are silently
    skipped so the caller never crashes on unexpected input.
    """
    # Collect tools that have the required structure, skipping malformed ones.
    valid_tools: list[dict[str, Any]] = []
    for tool in tools:
        func = tool.get("function") if isinstance(tool, dict) else None
        if not isinstance(func, dict) or not isinstance(func.get("name"), str):
            # Strip internal metadata even from malformed entries.
            if isinstance(func, dict):
                func.pop("_hardcoded_defaults", None)
            continue
        valid_tools.append(tool)

    names = [t.get("function", {}).get("name", "") for t in valid_tools]
    name_counts = Counter(names)
    duplicates = {n for n, c in name_counts.items() if c > 1}

    if not duplicates:
        for t in valid_tools:
            t.get("function", {}).pop("_hardcoded_defaults", None)
        return

    taken: set[str] = set(names)
    counters: dict[str, int] = {}

    for tool in valid_tools:
        func = tool.get("function", {})
        name = func.get("name", "")
        defaults = func.pop("_hardcoded_defaults", {})

        if name not in duplicates:
            continue

        counters[name] = counters.get(name, 0) + 1
        # Skip suffixes that collide with existing (e.g. user-named) tools
        while True:
            suffix = f"_{counters[name]}"
            candidate = f"{name[: 64 - len(suffix)]}{suffix}"
            if candidate not in taken:
                break
            counters[name] += 1

        func["name"] = candidate
        taken.add(candidate)

        if defaults and isinstance(defaults, dict):
            parts: list[str] = []
            for k, v in defaults.items():
                rendered = json.dumps(v)
                if len(rendered) > 100:
                    rendered = rendered[:80] + "...<truncated>"
                parts.append(f"{k}={rendered}")
            summary = ", ".join(parts)
            original_desc = func.get("description", "") or ""
            func["description"] = f"{original_desc} [Pre-configured: {summary}]"