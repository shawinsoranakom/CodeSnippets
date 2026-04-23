def bitwise_xor(cls, a, b):
        a, b = ValueRanges.wrap(a), ValueRanges.wrap(b)
        if a.is_bool and b.is_bool:
            bounds = {
                a.lower ^ b.lower,
                a.lower ^ b.upper,
                a.upper ^ b.lower,
                a.upper ^ b.upper,
            }

            has_false = any(bound == sympy.false for bound in bounds)
            has_true = any(bound == sympy.true for bound in bounds)

            if has_false and has_true:
                lower, upper = sympy.false, sympy.true
            elif has_true:
                lower = upper = sympy.true
            elif has_false:
                lower = upper = sympy.false
            else:
                raise AssertionError(f"Non-boolean xor result: {bounds}")

            return ValueRanges(lower, upper)
        if a.is_bool:
            a = cls._bool_to_int(a)
        if b.is_bool:
            b = cls._bool_to_int(b)
        if (
            a.lower == a.upper
            and b.lower == b.upper
            and is_sympy_integer(a.lower)
            and is_sympy_integer(b.lower)
        ):
            value_range = a.lower ^ b.lower
            return ValueRanges(value_range, value_range)
        return ValueRanges(-int_oo, int_oo)