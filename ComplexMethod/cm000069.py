def solution(order: int = 35) -> int:
    """
    Find the sum of the numerator and denominator of the sum of all s(x,y,z) for
    golden triples (x,y,z) of the given order.

    >>> solution(5)
    296
    >>> solution(10)
    12519
    >>> solution(20)
    19408891927
    """
    unique_s: set = set()
    hcf: int
    total: Fraction = Fraction(0)
    fraction_sum: tuple[int, int]

    for x_num in range(1, order + 1):
        for x_den in range(x_num + 1, order + 1):
            for y_num in range(1, order + 1):
                for y_den in range(y_num + 1, order + 1):
                    # n=1
                    z_num = x_num * y_den + x_den * y_num
                    z_den = x_den * y_den
                    hcf = gcd(z_num, z_den)
                    z_num //= hcf
                    z_den //= hcf
                    if 0 < z_num < z_den <= order:
                        fraction_sum = add_three(
                            x_num, x_den, y_num, y_den, z_num, z_den
                        )
                        unique_s.add(fraction_sum)

                    # n=2
                    z_num = (
                        x_num * x_num * y_den * y_den + x_den * x_den * y_num * y_num
                    )
                    z_den = x_den * x_den * y_den * y_den
                    if is_sq(z_num) and is_sq(z_den):
                        z_num = int(sqrt(z_num))
                        z_den = int(sqrt(z_den))
                        hcf = gcd(z_num, z_den)
                        z_num //= hcf
                        z_den //= hcf
                        if 0 < z_num < z_den <= order:
                            fraction_sum = add_three(
                                x_num, x_den, y_num, y_den, z_num, z_den
                            )
                            unique_s.add(fraction_sum)

                    # n=-1
                    z_num = x_num * y_num
                    z_den = x_den * y_num + x_num * y_den
                    hcf = gcd(z_num, z_den)
                    z_num //= hcf
                    z_den //= hcf
                    if 0 < z_num < z_den <= order:
                        fraction_sum = add_three(
                            x_num, x_den, y_num, y_den, z_num, z_den
                        )
                        unique_s.add(fraction_sum)

                    # n=2
                    z_num = x_num * x_num * y_num * y_num
                    z_den = (
                        x_den * x_den * y_num * y_num + x_num * x_num * y_den * y_den
                    )
                    if is_sq(z_num) and is_sq(z_den):
                        z_num = int(sqrt(z_num))
                        z_den = int(sqrt(z_den))
                        hcf = gcd(z_num, z_den)
                        z_num //= hcf
                        z_den //= hcf
                        if 0 < z_num < z_den <= order:
                            fraction_sum = add_three(
                                x_num, x_den, y_num, y_den, z_num, z_den
                            )
                            unique_s.add(fraction_sum)

    for num, den in unique_s:
        total += Fraction(num, den)

    return total.denominator + total.numerator