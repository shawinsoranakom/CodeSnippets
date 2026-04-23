def merge_lists(left: list | None, *others: list | None) -> list | None:
    """Add many lists, handling `None`.

    Args:
        left: The first list to merge.
        others: The other lists to merge.

    Returns:
        The merged list.
    """
    merged = left.copy() if left is not None else None
    for other in others:
        if other is None:
            continue
        if merged is None:
            merged = other.copy()
        else:
            for e in other:
                if (
                    isinstance(e, dict)
                    and "index" in e
                    and (
                        isinstance(e["index"], int)
                        or (
                            isinstance(e["index"], str) and e["index"].startswith("lc_")
                        )
                    )
                ):
                    to_merge = [
                        i
                        for i, e_left in enumerate(merged)
                        if (
                            "index" in e_left
                            and e_left["index"] == e["index"]  # index matches
                            and (  # IDs not inconsistent
                                e_left.get("id") in (None, "")
                                or e.get("id") in (None, "")
                                or e_left.get("id") == e.get("id")
                            )
                        )
                    ]
                    if to_merge:
                        # TODO: Remove this once merge_dict is updated with special
                        # handling for 'type'.
                        if (left_type := merged[to_merge[0]].get("type")) and (
                            e.get("type") == "non_standard" and "value" in e
                        ):
                            if left_type != "non_standard":
                                # standard + non_standard
                                new_e: dict[str, Any] = {
                                    "extras": {
                                        k: v
                                        for k, v in e["value"].items()
                                        if k != "type"
                                    }
                                }
                            else:
                                # non_standard + non_standard
                                new_e = {
                                    "value": {
                                        k: v
                                        for k, v in e["value"].items()
                                        if k != "type"
                                    }
                                }
                                if "index" in e:
                                    new_e["index"] = e["index"]
                        else:
                            new_e = (
                                {k: v for k, v in e.items() if k != "type"}
                                if "type" in e
                                else e
                            )
                        merged[to_merge[0]] = merge_dicts(merged[to_merge[0]], new_e)
                    else:
                        merged.append(e)
                else:
                    merged.append(e)
    return merged