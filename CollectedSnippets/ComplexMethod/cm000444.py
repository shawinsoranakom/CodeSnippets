def _assign(container: Any, tokens: list[tuple[str, str]], value: Any) -> Any:
    """
    Recursive helper that *returns* the (possibly new) container with
    `value` assigned along the remaining `tokens` path.
    """
    if not tokens:
        return value  # leaf reached

    delim, ident = tokens[0]
    rest = tokens[1:]

    # ---------- list ----------
    if delim == LIST_SPLIT:
        try:
            idx = int(ident)
        except ValueError:
            raise ValueError("index must be an integer")

        if container is None:
            container = []
        elif not isinstance(container, list):
            container = list(container) if hasattr(container, "__iter__") else []

        while len(container) <= idx:
            container.append(None)
        container[idx] = _assign(container[idx], rest, value)
        return container

    # ---------- dict ----------
    if delim == DICT_SPLIT:
        if container is None:
            container = {}
        elif not isinstance(container, dict):
            container = dict(container) if hasattr(container, "items") else {}
        container[ident] = _assign(container.get(ident), rest, value)
        return container

    # ---------- object ----------
    if delim == OBJC_SPLIT:
        if container is None:
            container = MockObject()
        elif not hasattr(container, "__dict__"):
            # If it's not an object, create a new one
            container = MockObject()
        setattr(
            container,
            ident,
            _assign(getattr(container, ident, None), rest, value),
        )
        return container

    return value