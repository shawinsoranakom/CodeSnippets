def generate_range(vals):
    for a1, a2 in itertools.product(vals, repeat=2):
        if a1 in [sympy.true, sympy.false]:
            if a1 == sympy.true and a2 == sympy.false:
                continue
        else:
            if a1 > a2:
                continue
        # ranges that only admit infinite values are not interesting
        if a1 == sympy.oo or a2 == -sympy.oo:
            continue
        yield ValueRanges(a1, a2)