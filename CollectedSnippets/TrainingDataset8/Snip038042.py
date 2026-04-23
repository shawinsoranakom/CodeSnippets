def _build_st_write_call(nodes):
    """Build AST node for `__streamlitmagic__.transparent_write(*nodes)`."""
    return ast.Call(
        func=ast.Attribute(
            attr="transparent_write",
            value=ast.Name(id=MAGIC_MODULE_NAME, ctx=ast.Load()),
            ctx=ast.Load(),
        ),
        args=nodes,
        keywords=[],
        kwargs=None,
        starargs=None,
    )