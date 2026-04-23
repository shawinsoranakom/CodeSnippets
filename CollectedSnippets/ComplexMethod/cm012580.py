def rewrite_float_subexpr(node: sympy.Expr) -> sympy.Expr:
        if not node.has(TruncToInt):
            return node
        if node.func is TruncToInt:
            return TruncToFloat(*node.args)
        if is_predicate_expr(node) or node.is_integer:
            return node

        new_args = tuple(
            rewrite_float_subexpr(arg)
            if isinstance(arg, sympy.Expr) and not is_predicate_expr(arg)
            else arg
            for arg in node.args
        )
        if new_args == node.args:
            return node
        return node.func(*new_args)