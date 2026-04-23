def eval(cls, base, divisor):
        if divisor.is_zero:
            raise ZeroDivisionError("division by zero")

        if (
            isinstance(base, sympy.Number)
            and isinstance(divisor, sympy.Number)
            and (is_infinite(base) or is_infinite(divisor))
        ):
            # Don't have to worry about precision here, you're getting zero or
            # inf from the division
            return sympy.Float(float(base) / float(divisor))
        if isinstance(base, sympy.Integer) and isinstance(divisor, sympy.Integer):
            return sympy.Float(int(base) / int(divisor))