def bitwise_or(cls, a, b):
        a, b = ValueRanges.wrap(a), ValueRanges.wrap(b)
        if a.is_bool and b.is_bool:
            return cls.or_(a, b)
        if a.is_bool:
            a = cls._bool_to_int(a)
        if b.is_bool:
            b = cls._bool_to_int(b)
        upper = max(a.upper, b.upper)
        if upper == 0:
            upper = 0
        elif upper > 0 and upper != sympy.oo and upper != int_oo:
            # If both upper bounds are positive, then the largest
            # possible value is 01...1, so we need to find
            # next largest power of 2 (exclusive), minus 1
            try:
                upper = (1 << int(upper).bit_length()) - 1
            except Exception:
                upper = int_oo
        elif upper < 0:
            upper = -1
        return ValueRanges(min(a.lower, b.lower), upper)