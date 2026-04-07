def get_children_from_q(q):
    for child in q.children:
        if isinstance(child, Node):
            yield from get_children_from_q(child)
        elif isinstance(child, tuple):
            lhs, rhs = child
            yield lhs
            if hasattr(rhs, "resolve_expression"):
                yield from get_paths_from_expression(rhs)
        elif hasattr(child, "resolve_expression"):
            yield from get_paths_from_expression(child)