def floordiv(a, b):
        a = ValueRanges.wrap(a)
        b = ValueRanges.wrap(b)

        # TODO We shall assume division is always valid probably.
        if 0 in b:
            if b.lower >= 0 and a.lower >= 0:
                return ValueRanges(0, int_oo)
            if b.upper <= 0 and a.upper <= 0:
                return ValueRanges(0, int_oo)
            if b.upper <= 0 and a.lower >= 0:
                return ValueRanges(-int_oo, 0)
            if b.lower >= 0 and a.upper <= 0:
                return ValueRanges(-int_oo, 0)
            return ValueRanges.unknown_int()
        products = []
        for x, y in itertools.product([a.lower, a.upper], [b.lower, b.upper]):
            r = FloorDiv(x, y)
            if r is sympy.nan:
                products.append((sympy.sign(x) * sympy.sign(y)) * int_oo)
            else:
                products.append(r)

        return ValueRanges(min(products), max(products))