def _sorted_items(state: SessionState) -> List[Tuple[str, Any]]:
    """Return all key-value pairs in the SessionState.
    The returned list is sorted by key for easier comparison.
    """
    return [(key, state[key]) for key in sorted(state._keys())]