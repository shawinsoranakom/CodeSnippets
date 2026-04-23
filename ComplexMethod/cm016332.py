def expand_hints(hints: list[str], dynamo_dir: str | None = None) -> list[str]:
    """
    Expands hint references to their actual values from graph_break_hints.
    Uses exec() to avoid import dependencies.
    """
    if dynamo_dir is None:
        script_dir = Path(__file__).resolve().parent
        dynamo_dir_path = script_dir.parent.parent / "torch" / "_dynamo"
    else:
        dynamo_dir_path = Path(dynamo_dir)

    graph_break_hints_path = dynamo_dir_path / "graph_break_hints.py"

    with open(graph_break_hints_path) as f:
        hints_source = f.read()

    hints_namespace: dict[str, Any] = {}
    exec(hints_source, hints_namespace)

    hint_constants = {
        name: value
        for name, value in hints_namespace.items()
        if isinstance(value, list) and name.isupper() and not name.startswith("_")
    }

    expanded_hints = []
    for hint in hints:
        expanded = False
        for name, value in hint_constants.items():
            if f"*graph_break_hints.{name}" in hint:
                expanded_hints.extend(value)
                expanded = True
                break
        if not expanded:
            expanded_hints.append(hint)

    return expanded_hints