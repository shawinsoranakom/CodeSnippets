def _get_expression_contextual_values(item_ast):
    """ Return all contextual value this ast

    eg: ast from '''(
            id in [1, 2, 3]
            and field_a in parent.truc
            and field_b in context.get('b')
            or (
                True
                and bool(context.get('c'))
            )
        )
        returns {'parent', 'parent.truc', 'context', 'bool'}

    :param item_ast: ast
    :return: set(str)
    """

    if isinstance(item_ast, ast.Constant):
        return set()
    if isinstance(item_ast, (ast.List, ast.Tuple)):
        values = set()
        for item in item_ast.elts:
            values |= _get_expression_contextual_values(item)
        return values
    if isinstance(item_ast, ast.Name):
        return {item_ast.id}
    if isinstance(item_ast, ast.Attribute):
        values = _get_expression_contextual_values(item_ast.value)
        if len(values) == 1:
            path = sorted(list(values)).pop()
            values = {f"{path}.{item_ast.attr}"}
            return values
        return values
    if isinstance(item_ast, ast.Index): # deprecated python ast class for Subscript key
        return _get_expression_contextual_values(item_ast.value)
    if isinstance(item_ast, ast.Subscript):
        values = _get_expression_contextual_values(item_ast.value)
        values |= _get_expression_contextual_values(item_ast.slice)
        return values
    if isinstance(item_ast, ast.Compare):
        values = _get_expression_contextual_values(item_ast.left)
        for sub_ast in item_ast.comparators:
            values |= _get_expression_contextual_values(sub_ast)
        return values
    if isinstance(item_ast, ast.BinOp):
        values = _get_expression_contextual_values(item_ast.left)
        values |= _get_expression_contextual_values(item_ast.right)
        return values
    if isinstance(item_ast, ast.BoolOp):
        values = set()
        for ast_value in item_ast.values:
            values |= _get_expression_contextual_values(ast_value)
        return values
    if isinstance(item_ast, ast.UnaryOp):
        return _get_expression_contextual_values(item_ast.operand)
    if isinstance(item_ast, ast.Call):
        values = _get_expression_contextual_values(item_ast.func)
        for ast_arg in item_ast.args:
            values |= _get_expression_contextual_values(ast_arg)
        return values
    if isinstance(item_ast, ast.IfExp):
        values = _get_expression_contextual_values(item_ast.test)
        values |= _get_expression_contextual_values(item_ast.body)
        values |= _get_expression_contextual_values(item_ast.orelse)
        return values
    if isinstance(item_ast, ast.Dict):
        values = set()
        for item in item_ast.keys:
            values |= _get_expression_contextual_values(item)
        for item in item_ast.values:
            values |= _get_expression_contextual_values(item)
        return values

    raise ValueError(f"Undefined item {item_ast!r}.")