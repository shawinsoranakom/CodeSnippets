def get_paths_from_expression(expr):
    if isinstance(expr, F):
        yield expr.name
    elif hasattr(expr, "flatten"):
        for child in expr.flatten():
            if isinstance(child, F):
                yield child.name
            elif isinstance(child, Q):
                yield from get_children_from_q(child)