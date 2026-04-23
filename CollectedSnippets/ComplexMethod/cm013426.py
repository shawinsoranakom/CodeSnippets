def _format_arg(arg: object, max_list_len: float = float("inf")) -> str:
    if hasattr(arg, "_custom_fx_repr_fn"):
        return arg._custom_fx_repr_fn()
    elif isinstance(arg, list):
        items = ", ".join(
            _format_arg(a) for idx, a in enumerate(arg) if idx < max_list_len
        )
        maybe_len = (
            "" if len(arg) < max_list_len + 1 else f", ...[total_len={len(arg)}]"
        )
        return f"[{items}{maybe_len}]"
    elif isinstance(arg, tuple):
        items = ", ".join(
            _format_arg(a) for idx, a in enumerate(arg) if idx < max_list_len
        )
        maybe_len = (
            "" if len(arg) < max_list_len + 1 else f", ...[total_len={len(arg)}]"
        )
        maybe_comma = "," if len(arg) == 1 else ""
        return f"({items}{maybe_comma}{maybe_len})"
    elif isinstance(arg, dict):
        items_str = ", ".join(f"{k}: {_format_arg(v)}" for k, v in arg.items())
        return f"{{{items_str}}}"

    if isinstance(arg, Node):
        return "%" + str(arg)
    else:
        return str(arg)