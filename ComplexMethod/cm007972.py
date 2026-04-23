def js_number_to_string(val: float, radix: int = 10):
    if radix in (JS_Undefined, None):
        radix = 10
    assert radix in range(2, 37), 'radix must be an integer at least 2 and no greater than 36'

    if math.isnan(val):
        return 'NaN'
    if val == 0:
        return '0'
    if math.isinf(val):
        return '-Infinity' if val < 0 else 'Infinity'
    if radix == 10:
        # TODO: implement special cases
        ...

    ALPHABET = b'0123456789abcdefghijklmnopqrstuvwxyz.-'

    result = collections.deque()
    sign = val < 0
    val = abs(val)
    fraction, integer = math.modf(val)
    delta = max(math.nextafter(.0, math.inf), math.ulp(val) / 2)

    if fraction >= delta:
        result.append(-2)  # `.`
    while fraction >= delta:
        delta *= radix
        fraction, digit = math.modf(fraction * radix)
        result.append(int(digit))
        # if we need to round, propagate potential carry through fractional part
        needs_rounding = fraction > 0.5 or (fraction == 0.5 and int(digit) & 1)
        if needs_rounding and fraction + delta > 1:
            for index in reversed(range(1, len(result))):
                if result[index] + 1 < radix:
                    result[index] += 1
                    break
                result.pop()

            else:
                integer += 1
            break

    integer, digit = divmod(int(integer), radix)
    result.appendleft(digit)
    while integer > 0:
        integer, digit = divmod(integer, radix)
        result.appendleft(digit)

    if sign:
        result.appendleft(-1)  # `-`

    return bytes(ALPHABET[digit] for digit in result).decode('ascii')