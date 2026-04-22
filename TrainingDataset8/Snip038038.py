def add_magic(code, script_path):
    """Modifies the code to support magic Streamlit commands.

    Parameters
    ----------
    code : str
        The Python code.
    script_path : str
        The path to the script file.

    Returns
    -------
    ast.Module
        The syntax tree for the code.

    """
    # Pass script_path so we get pretty exceptions.
    tree = ast.parse(code, script_path, "exec")
    return _modify_ast_subtree(tree, is_root=True)