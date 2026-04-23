def parse_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    module_path: str,
    src: str,
    *,
    parent: str | None = None,
    allow_private: bool = False,
) -> DocItem | None:
    """Parse a function or method node into a DocItem."""
    raw_docstring = ast.get_docstring(node)
    if not _should_document(node.name, allow_private=allow_private) and not raw_docstring:
        return None

    is_async = isinstance(node, ast.AsyncFunctionDef)
    doc = parse_google_docstring(raw_docstring)
    qualname = f"{module_path}.{node.name}" if not parent else f"{parent}.{node.name}"
    decorators = {_get_source(src, d).split(".")[-1] for d in node.decorator_list}
    kind: Literal["function", "method", "property"] = "method" if parent else "function"
    if decorators & PROPERTY_DECORATORS:
        kind = "property"

    signature_params = collect_signature_parameters(node.args, src, skip_self=bool(parent))

    return DocItem(
        name=node.name,
        qualname=qualname,
        kind=kind,
        signature=format_signature(node, src, is_async=is_async),
        doc=doc,
        signature_params=signature_params,
        lineno=node.lineno,
        end_lineno=node.end_lineno or node.lineno,
        bases=[],
        children=[],
        module_path=module_path,
        source=_collect_source_block(src, node),
    )