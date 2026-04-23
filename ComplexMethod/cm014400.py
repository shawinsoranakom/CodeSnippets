def bitwise_and(cls, a, b):
        a, b = ValueRanges.wrap(a), ValueRanges.wrap(b)
        if a.is_bool and b.is_bool:
            return cls.and_(a, b)
        if a.is_bool:
            a = cls._bool_to_int(a)
        if b.is_bool:
            b = cls._bool_to_int(b)
        lower = min(a.lower, b.lower)
        if lower < 0 and lower != -sympy.oo and lower != -int_oo:
            # If both lower bounds are negative, then bits start like
            # 1...10..., so the smallest possible value is 1...101...1.
            # Thus, we need to find the next smallest power of 2 (inclusive).
            try:
                lower = -(1 << int(-lower - 1).bit_length())
            except Exception:
                lower = -int_oo
        else:
            lower = 0
        return ValueRanges(lower, max(a.upper, b.upper))