def _node_ref(arg: Any) -> str:
    """Convert an FX node argument to a source code reference recursively."""
    if isinstance(arg, torch.fx.Node):
        return arg.name
    if isinstance(arg, list):
        return f"[{', '.join(_node_ref(x) for x in arg)}]"
    if isinstance(arg, tuple):
        items = ", ".join(_node_ref(x) for x in arg)
        return f"({items},)" if len(arg) == 1 else f"({items})"
    if isinstance(arg, dict):
        return (
            "{"
            + ", ".join(f"{_node_ref(k)}: {_node_ref(v)}" for k, v in arg.items())
            + "}"
        )
    return repr(arg)