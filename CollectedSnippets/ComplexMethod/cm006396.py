def _extract_io_names(tree: ast.Module, class_name: str) -> tuple[set[str], set[str]]:
    """Extract input and output names from component code using AST.

    Returns:
        Tuple of (input_names, output_names) as sets of strings.
    """
    class_node = _find_class_node(tree, class_name)
    if class_node is None:
        return set(), set()

    input_names: set[str] = set()
    inputs_list = _find_list_assign(class_node, "inputs")
    if inputs_list is not None:
        for elt in inputs_list.elts:
            if isinstance(elt, ast.Call):
                name = _extract_str_kwarg(elt, "name")
                if name is not None:
                    input_names.add(name)

    output_names: set[str] = set()
    outputs_list = _find_list_assign(class_node, "outputs")
    if outputs_list is not None:
        for elt in outputs_list.elts:
            if isinstance(elt, ast.Call):
                name = _extract_str_kwarg(elt, "name")
                if name is not None:
                    output_names.add(name)

    return input_names, output_names