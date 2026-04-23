def strtod(s, mant_dig=53, min_exp = -1021, max_exp = 1024):
    """Convert a finite decimal string to a hex string representing an
    IEEE 754 binary64 float.  Return 'inf' or '-inf' on overflow.
    This function makes no use of floating-point arithmetic at any
    stage."""

    # parse string into a pair of integers 'a' and 'b' such that
    # abs(decimal value) = a/b, along with a boolean 'negative'.
    m = strtod_parser(s)
    if m is None:
        raise ValueError('invalid numeric string')
    fraction = m.group('frac') or ''
    intpart = int(m.group('int') + fraction)
    exp = int(m.group('exp') or '0') - len(fraction)
    negative = m.group('sign') == '-'
    a, b = intpart*10**max(exp, 0), 10**max(0, -exp)

    # quick return for zeros
    if not a:
        return '-0x0.0p+0' if negative else '0x0.0p+0'

    # compute exponent e for result; may be one too small in the case
    # that the rounded value of a/b lies in a different binade from a/b
    d = a.bit_length() - b.bit_length()
    d += (a >> d if d >= 0 else a << -d) >= b
    e = max(d, min_exp) - mant_dig

    # approximate a/b by number of the form q * 2**e; adjust e if necessary
    a, b = a << max(-e, 0), b << max(e, 0)
    q, r = divmod(a, b)
    if 2*r > b or 2*r == b and q & 1:
        q += 1
        if q.bit_length() == mant_dig+1:
            q //= 2
            e += 1

    # double check that (q, e) has the right form
    assert q.bit_length() <= mant_dig and e >= min_exp - mant_dig
    assert q.bit_length() == mant_dig or e == min_exp - mant_dig

    # check for overflow and underflow
    if e + q.bit_length() > max_exp:
        return '-inf' if negative else 'inf'
    if not q:
        return '-0x0.0p+0' if negative else '0x0.0p+0'

    # for hex representation, shift so # bits after point is a multiple of 4
    hexdigs = 1 + (mant_dig-2)//4
    shift = 3 - (mant_dig-2)%4
    q, e = q << shift, e - shift
    return '{}0x{:x}.{:0{}x}p{:+d}'.format(
        '-' if negative else '',
        q // 16**hexdigs,
        q % 16**hexdigs,
        hexdigs,
        e + 4*hexdigs)