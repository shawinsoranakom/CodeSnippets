def _sqrtprod(x: float, y: float) -> float:
    "Return sqrt(x * y) computed with improved accuracy and without overflow/underflow."

    h = sqrt(x * y)

    if not isfinite(h):
        if isinf(h) and not isinf(x) and not isinf(y):
            # Finite inputs overflowed, so scale down, and recompute.
            scale = 2.0 ** -512  # sqrt(1 / sys.float_info.max)
            return _sqrtprod(scale * x, scale * y) / scale
        return h

    if not h:
        if x and y:
            # Non-zero inputs underflowed, so scale up, and recompute.
            # Scale:  1 / sqrt(sys.float_info.min * sys.float_info.epsilon)
            scale = 2.0 ** 537
            return _sqrtprod(scale * x, scale * y) / scale
        return h

    # Improve accuracy with a differential correction.
    # https://www.wolframalpha.com/input/?i=Maclaurin+series+sqrt%28h**2+%2B+x%29+at+x%3D0
    d = sumprod((x, h), (y, -h))
    return h + d / (2.0 * h)