def _insert_import_statement(tree):
    """Insert Streamlit import statement at the top(ish) of the tree."""

    st_import = _build_st_import_statement()

    # If the 0th node is already an import statement, put the Streamlit
    # import below that, so we don't break "from __future__ import".
    if tree.body and type(tree.body[0]) in (ast.ImportFrom, ast.Import):
        tree.body.insert(1, st_import)

    # If the 0th node is a docstring and the 1st is an import statement,
    # put the Streamlit import below those, so we don't break "from
    # __future__ import".
    elif (
        len(tree.body) > 1
        and (type(tree.body[0]) is ast.Expr and _is_docstring_node(tree.body[0].value))
        and type(tree.body[1]) in (ast.ImportFrom, ast.Import)
    ):
        tree.body.insert(2, st_import)

    else:
        tree.body.insert(0, st_import)