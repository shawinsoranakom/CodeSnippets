def extended_gcd(a: int, b: int) -> tuple[int, int, int]:
    
    assert a >= 0
    assert b >= 0

    if b == 0:
        d, x, y = a, 1, 0
    else:
        (d, p, q) = extended_gcd(b, a % b)
        x = q
        y = p - q * (a // b)

    assert a % d == 0
    assert b % d == 0
    assert d == a * x + b * y

    return (d, x, y)
