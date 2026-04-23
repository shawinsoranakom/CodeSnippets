def normalize_flow(
    flow: dict[str, Any],
    *,
    strip_volatile: bool = True,
    strip_secrets: bool = True,
    sort_keys: bool = True,
    code_as_lines: bool = False,
    strip_node_volatile: bool = True,
) -> dict[str, Any]:
    """Return a git-friendly copy of *flow*.

    Parameters
    ----------
    flow:
        Raw flow dict as returned by the Langflow API or read from a ``.json``
        file.
    strip_volatile:
        Remove top-level fields that carry instance-specific state
        (``updated_at``, ``user_id``, ``folder_id``, ``created_at``).
    strip_secrets:
        Clear ``value`` on template fields marked ``password=True`` or
        ``load_from_db=True``.
    sort_keys:
        Recursively sort all dict keys so the output is deterministic.
    code_as_lines:
        Convert ``type="code"`` template field values from a single string
        to a list of lines for cleaner per-line diffs.
    strip_node_volatile:
        Remove ``positionAbsolute``, ``dragging``, and ``selected`` keys from
        individual nodes (they change whenever a node is dragged in the UI).

    Returns:
    -------
    dict[str, Any]
        A new dict -- the original is never mutated.
    """
    result: dict[str, Any] = copy.deepcopy(flow)

    if strip_volatile:
        for key in _VOLATILE_TOP_LEVEL:
            result.pop(key, None)

    data: dict[str, Any] = dict(result.get("data") or {})
    nodes: list[Any] = list(data.get("nodes") or [])

    processed_nodes = [
        _process_node(
            n,
            strip_secrets=strip_secrets,
            code_as_lines=code_as_lines,
            strip_node_volatile=strip_node_volatile,
        )
        if isinstance(n, dict)
        else n
        for n in nodes
    ]
    data["nodes"] = processed_nodes
    result["data"] = data

    if sort_keys:
        result = _sort_recursive(result)

    return result