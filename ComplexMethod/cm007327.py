def _operator(self, op, left_val, right_expr, expr, local_vars, allow_recursion):
        if op in ('||', '&&'):
            if (op == '&&') ^ _js_ternary(left_val):
                return left_val  # short circuiting
        elif op == '??':
            if left_val not in (None, JS_Undefined):
                return left_val
        elif op == '?':
            right_expr = _js_ternary(left_val, *self._separate(right_expr, ':', 1))

        right_val = self.interpret_expression(right_expr, local_vars, allow_recursion) if right_expr else left_val
        opfunc = op and next((v for k, v in self._all_operators() if k == op), None)
        if not opfunc:
            return right_val

        try:
            # print('Eval:', opfunc.__name__, left_val, right_val)
            return opfunc(left_val, right_val)
        except Exception as e:
            raise self.Exception('Failed to evaluate {left_val!r:.50} {op} {right_val!r:.50}'.format(**locals()), expr, cause=e)