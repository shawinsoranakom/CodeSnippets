def _maybe_tuple_to_list(item: Any) -> Any:
    """Convert a tuple to a list. Leave as is if it's not a tuple."""
    if isinstance(item, tuple):
        return list(item)
    return item