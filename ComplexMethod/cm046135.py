def parse_class(node: ast.ClassDef, module_path: str, src: str) -> DocItem:
    """Parse a class node, merging __init__ docs and collecting methods."""
    class_doc = parse_google_docstring(ast.get_docstring(node))

    init_node: ast.FunctionDef | ast.AsyncFunctionDef | None = next(
        (n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "__init__"),
        None,
    )
    signature_params: list[ParameterDoc] = []
    if init_node:
        init_doc = parse_google_docstring(ast.get_docstring(init_node))
        class_doc = merge_docstrings(class_doc, init_doc, ignore_summary=True)
        signature_params = collect_signature_parameters(init_node.args, src, skip_self=True)

    bases = [_get_source(src, b) for b in node.bases] if node.bases else []
    signature_node = init_node or node
    class_signature = format_signature(signature_node, src, is_class=True, display_name=node.name)

    methods: list[DocItem] = []
    for child in node.body:
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child is not init_node:
            method_doc = parse_function(child, module_path, src, parent=f"{module_path}.{node.name}")
            if method_doc:
                methods.append(method_doc)

    return DocItem(
        name=node.name,
        qualname=f"{module_path}.{node.name}",
        kind="class",
        signature=class_signature,
        doc=class_doc,
        signature_params=signature_params,
        lineno=node.lineno,
        end_lineno=node.end_lineno or node.lineno,
        bases=bases,
        children=methods,
        module_path=module_path,
        source=_collect_source_block(src, node, end_line=init_node.end_lineno if init_node else node.lineno),
    )