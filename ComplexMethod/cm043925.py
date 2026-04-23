def _nearest_non_bop_ancestor_title(parent_id: Any) -> str | None:
        pid = str(parent_id) if parent_id else ""
        safety = 0
        while pid and safety < 50:
            safety += 1
            parent_df = _lookup_parent_row(pid)
            if len(parent_df) == 0:
                return None
            parent_first = parent_df.iloc[0]
            parent_title = _normalize_title(str(parent_first.get("title") or ""))
            if (
                parent_title
                and not is_bop_suffix_only(parent_title)
                and not parent_title.endswith((", Net", ", Credit", ", Debit"))
            ):
                return parent_title
            pid = str(parent_first.get("parent_id") or "")
        return None