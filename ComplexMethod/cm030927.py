def truediv(a, b):
    """Correctly-rounded true division for integers."""
    negative = a^b < 0
    a, b = abs(a), abs(b)

    # exceptions:  division by zero, overflow
    if not b:
        raise ZeroDivisionError("division by zero")
    if a >= DBL_MIN_OVERFLOW * b:
        raise OverflowError("int/int too large to represent as a float")

   # find integer d satisfying 2**(d - 1) <= a/b < 2**d
    d = a.bit_length() - b.bit_length()
    if d >= 0 and a >= 2**d * b or d < 0 and a * 2**-d >= b:
        d += 1

    # compute 2**-exp * a / b for suitable exp
    exp = max(d, DBL_MIN_EXP) - DBL_MANT_DIG
    a, b = a << max(-exp, 0), b << max(exp, 0)
    q, r = divmod(a, b)

    # round-half-to-even: fractional part is r/b, which is > 0.5 iff
    # 2*r > b, and == 0.5 iff 2*r == b.
    if 2*r > b or 2*r == b and q % 2 == 1:
        q += 1

    result = math.ldexp(q, exp)
    return -result if negative else result