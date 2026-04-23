def _operator(self, op, left_val, right_expr, expr, local_vars, allow_recursion):
        if op in ('||', '&&'):
            if (op == '&&') ^ _js_ternary(left_val):
                return left_val  # short circuiting
        elif op == '??':
            if left_val not in (None, JS_Undefined):
                return left_val
        elif op == '?':
            right_expr = _js_ternary(left_val, *self._separate(right_expr, ':', 1))

        right_val = self.interpret_expression(right_expr, local_vars, allow_recursion)
        if not _OPERATORS.get(op):
            return right_val

        # TODO: This is only correct for str+str and str+number; fix for str+array, str+object, etc
        if op == '+' and (isinstance(left_val, str) or isinstance(right_val, str)):
            return f'{left_val}{right_val}'

        try:
            return _OPERATORS[op](left_val, right_val)
        except Exception as e:
            raise self.Exception(f'Failed to evaluate {left_val!r} {op} {right_val!r}', expr, cause=e)