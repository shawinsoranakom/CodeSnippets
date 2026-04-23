def make_terse(
    blocks: Sequence[dict[str, Any]],
    index_by_line: bool = True,
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}

    max_line = max(b["start_line"] for b in blocks) if blocks else 0
    line_field_width = len(str(max_line))

    for b in blocks:
        root = f"{b['category']} {b['full_name']}"
        for i in itertools.count():
            name = root + bool(i) * f"[{i + 1}]"
            if name not in result:
                break

        d = {
            "docstring_len": len(b["docstring"]),
            "lines": b["line_count"],
            "status": b.get("status", "good"),
        }

        start_line = b["start_line"]
        if index_by_line:
            d["name"] = name
            result[f"{start_line:>{line_field_width}}"] = d
        else:
            d["line"] = start_line
            result[name] = d

        if kids := b["children"]:
            if not all(isinstance(k, int) for k in kids):
                if not all(isinstance(k, dict) for k in kids):
                    raise AssertionError("children must be all int or all dict")
                d["children"] = make_terse(kids)

    return result