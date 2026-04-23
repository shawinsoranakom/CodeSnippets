def _modify_ast_subtree(tree, body_attr="body", is_root=False):
    """Parses magic commands and modifies the given AST (sub)tree."""

    body = getattr(tree, body_attr)

    for i, node in enumerate(body):
        node_type = type(node)

        # Parse the contents of functions, With statements, and for statements
        if (
            node_type is ast.FunctionDef
            or node_type is ast.With
            or node_type is ast.For
            or node_type is ast.While
            or node_type is ast.AsyncFunctionDef
            or node_type is ast.AsyncWith
            or node_type is ast.AsyncFor
        ):
            _modify_ast_subtree(node)

        # Parse the contents of try statements
        elif node_type is ast.Try:
            for j, inner_node in enumerate(node.handlers):
                node.handlers[j] = _modify_ast_subtree(inner_node)
            finally_node = _modify_ast_subtree(node, body_attr="finalbody")
            node.finalbody = finally_node.finalbody
            _modify_ast_subtree(node)

        # Convert if expressions to st.write
        elif node_type is ast.If:
            _modify_ast_subtree(node)
            _modify_ast_subtree(node, "orelse")

        # Convert standalone expression nodes to st.write
        elif node_type is ast.Expr:
            value = _get_st_write_from_expr(node, i, parent_type=type(tree))
            if value is not None:
                node.value = value

    if is_root:
        # Import Streamlit so we can use it in the new_value above.
        _insert_import_statement(tree)

    ast.fix_missing_locations(tree)

    return tree