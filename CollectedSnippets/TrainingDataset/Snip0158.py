def diophantine(a: int, b: int, c: int) -> tuple[float, float]:
    
    assert (
        c % greatest_common_divisor(a, b) == 0
    )  
    (d, x, y) = extended_gcd(a, b)  
    r = c / d
    return (r * x, r * y)
