def format_signature(
    node: ast.AST, src: str, *, is_class: bool = False, is_async: bool = False, display_name: str | None = None
) -> str:
    """Build a readable signature string for classes, functions, and methods."""
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return ""

    if isinstance(node, ast.ClassDef):
        init_method = next(
            (n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "__init__"),
            None,
        )
        args = (
            init_method.args
            if init_method
            else ast.arguments(
                posonlyargs=[], args=[], vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]
            )
        )
    else:
        args = node.args
    name = display_name or getattr(node, "name", "")
    params: list[str] = []

    posonly = list(getattr(args, "posonlyargs", []))
    regular = list(getattr(args, "args", []))
    defaults = list(getattr(args, "defaults", []))
    total_regular = len(posonly) + len(regular)
    default_offset = total_regular - len(defaults)

    combined = posonly + regular
    for idx, arg in enumerate(combined):
        default = defaults[idx - default_offset] if idx >= default_offset else None
        params.append(_format_parameter(arg, default, src))
        if posonly and idx == len(posonly) - 1:
            params.append("/")

    vararg = getattr(args, "vararg", None)
    if vararg:
        rendered = _format_parameter(vararg, None, src)
        params.append(f"*{rendered}")

    kwonly = list(getattr(args, "kwonlyargs", []))
    kw_defaults = list(getattr(args, "kw_defaults", []))
    if kwonly:
        if not vararg:
            params.append("*")
        for kwarg, default in zip(kwonly, kw_defaults):
            params.append(_format_parameter(kwarg, default, src))

    kwarg = getattr(args, "kwarg", None)
    if kwarg:
        rendered = _format_parameter(kwarg, None, src)
        params.append(f"**{rendered}")

    return_annotation = (
        _format_annotation(node.returns, src)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.returns
        else None
    )

    prefix = "" if is_class else ("async def " if is_async else "def ")
    signature = f"{prefix}{name}({', '.join(params)})"
    if return_annotation:
        signature += f" -> {return_annotation}"

    if len(signature) <= SIGNATURE_LINE_LENGTH or not params:
        return signature

    raw_signature = _get_definition_signature(node, src)
    return raw_signature or signature