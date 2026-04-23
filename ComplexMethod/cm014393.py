def eval(cls, a, b):
            if a.is_Boolean and b.is_Boolean:
                return getattr(operator, real_op_name)(a, b)
            if a.is_Boolean:
                a = sympy.Integer(1 if a else 0)
            if b.is_Boolean:
                b = sympy.Integer(1 if b else 0)
            if isinstance(a, (sympy.Integer, int)) and isinstance(
                b, (sympy.Integer, int)
            ):
                return sympy.Integer(getattr(operator, real_op_name)(int(a), int(b)))
            return None