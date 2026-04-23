def _is_docstring_node(node):
    if sys.version_info >= (3, 8, 0):
        return type(node) is ast.Constant and type(node.value) is str
    else:
        return type(node) is ast.Str