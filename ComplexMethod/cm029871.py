def _convert_literal(node):
    """
    Used by `literal_eval` to convert an AST node into a value.
    """
    if isinstance(node, Constant):
        return node.value
    if isinstance(node, Dict) and len(node.keys) == len(node.values):
        return dict(zip(
            map(_convert_literal, node.keys),
            map(_convert_literal, node.values),
        ))
    if isinstance(node, Tuple):
        return tuple(map(_convert_literal, node.elts))
    if isinstance(node, List):
        return list(map(_convert_literal, node.elts))
    if isinstance(node, Set):
        return set(map(_convert_literal, node.elts))
    if (
        isinstance(node, Call) and isinstance(node.func, Name)
        and node.func.id == 'set' and node.args == node.keywords == []
    ):
        return set()
    if (
        isinstance(node, UnaryOp)
        and isinstance(node.op, (UAdd, USub))
        and isinstance(node.operand, Constant)
        and type(operand := node.operand.value) in (int, float, complex)
    ):
        if isinstance(node.op, UAdd):
            return + operand
        else:
            return - operand
    if (
        isinstance(node, BinOp)
        and isinstance(node.op, (Add, Sub))
        and isinstance(node.left, (Constant, UnaryOp))
        and isinstance(node.right, Constant)
        and type(left := _convert_literal(node.left)) in (int, float)
        and type(right := _convert_literal(node.right)) is complex
    ):
        if isinstance(node.op, Add):
            return left + right
        else:
            return left - right
    msg = "malformed node or string"
    if lno := getattr(node, 'lineno', None):
        msg += f' on line {lno}'
    raise ValueError(msg + f': {node!r}')