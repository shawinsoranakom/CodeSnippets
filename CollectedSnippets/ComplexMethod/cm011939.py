def _join_dimensions_cached(expr: Expr) -> Expr:
    """
    ModularIndexing(i0, 1, 32) + 32 * ModularIndexing(i0, 32, 4)
    becomes
    ModularIndexing(i0, 1, 128)
    ModularIndexing(i0, 1, 32) + 32 * FloorDiv(i0, 32)
    becomes i0


    This type of pattern can come from view operations
    """
    assert isinstance(expr, sympy.Add)

    scale = sympy.Wild("scale", exclude=[0], integer=True)
    base = sympy.Wild("base", integer=True)
    divisor = sympy.Wild("divisor", integer=True)
    mod1 = sympy.Wild("modulus", integer=True)
    mod2 = sympy.Wild("modulus2", integer=True)
    for term1 in expr.args:
        m1 = term1.match(scale * ModularIndexing(base, divisor, mod1))
        if m1:
            for term2 in expr.args:
                m2 = term2.match(
                    m1[scale]
                    * m1[mod1]
                    * ModularIndexing(m1[base], m1[divisor] * m1[mod1], mod2)
                )
                if m2 and term1 != term2:
                    expr = join_dimensions(
                        expr
                        - term1
                        - term2
                        + m1[scale]
                        * ModularIndexing(m1[base], m1[divisor], m1[mod1] * m2[mod2])
                    )
                    return expr
    for term1 in expr.args:
        m1 = term1.match(scale * ModularIndexing(base, divisor, mod1))
        if m1:
            for term2 in expr.args:
                m2 = term2.match(
                    m1[scale] * m1[mod1] * FloorDiv(m1[base], m1[divisor] * m1[mod1])
                )
                if m2 is not None:  # in case of success we get an empty dict here
                    expr = join_dimensions(
                        expr
                        - term1
                        - term2
                        + m1[scale] * FloorDiv(m1[base], m1[divisor])
                    )
                    return expr
    return expr