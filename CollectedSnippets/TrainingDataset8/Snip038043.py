def _get_st_write_from_expr(node, i, parent_type):
    # Don't change function calls
    if type(node.value) is ast.Call:
        return None

    # Don't change Docstring nodes
    if (
        i == 0
        and _is_docstring_node(node.value)
        and parent_type in (ast.FunctionDef, ast.Module)
    ):
        return None

    # Don't change yield nodes
    if type(node.value) is ast.Yield or type(node.value) is ast.YieldFrom:
        return None

    # Don't change await nodes
    if type(node.value) is ast.Await:
        return None

    # If tuple, call st.write on the 0th element (rather than the
    # whole tuple). This allows us to add a comma at the end of a statement
    # to turn it into an expression that should be st-written. Ex:
    # "np.random.randn(1000, 2),"
    if type(node.value) is ast.Tuple:
        args = node.value.elts
        st_write = _build_st_write_call(args)

    # st.write all strings.
    elif type(node.value) is ast.Str:
        args = [node.value]
        st_write = _build_st_write_call(args)

    # st.write all variables.
    elif type(node.value) is ast.Name:
        args = [node.value]
        st_write = _build_st_write_call(args)

    # st.write everything else
    else:
        args = [node.value]
        st_write = _build_st_write_call(args)

    return st_write