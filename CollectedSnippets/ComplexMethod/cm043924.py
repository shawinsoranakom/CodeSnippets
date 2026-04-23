def _normalize_title(raw_title: str | None) -> str:
        title = (raw_title or "").lstrip()

        # Remove header marker (used for promoted headers in the rendered output)
        if title.startswith("▸"):
            title = title[1:].lstrip()

        # Strip parenthetical unit suffix
        if " (" in title and title.endswith(")"):
            paren_idx = title.rfind(" (")
            if paren_idx > 0:
                title = title[:paren_idx]

        # Strip common unit qualifiers that can trail titles
        unit_suffixes = [", Transactions", ", Stocks", ", Flows"]
        for suffix in unit_suffixes:
            if title.endswith(suffix):
                title = title[: -len(suffix)]
                break

        return title