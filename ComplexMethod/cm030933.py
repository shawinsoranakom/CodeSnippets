def __init__(self, value):
                if isinstance(value, int):
                    self.n = value
                    self.d = 1
                elif isinstance(value, float):
                    # Convert to exact rational equivalent.
                    f, e = math.frexp(abs(value))
                    assert f == 0 or 0.5 <= f < 1.0
                    # |value| = f * 2**e exactly

                    # Suck up CHUNK bits at a time; 28 is enough so that we suck
                    # up all bits in 2 iterations for all known binary double-
                    # precision formats, and small enough to fit in an int.
                    CHUNK = 28
                    top = 0
                    # invariant: |value| = (top + f) * 2**e exactly
                    while f:
                        f = math.ldexp(f, CHUNK)
                        digit = int(f)
                        assert digit >> CHUNK == 0
                        top = (top << CHUNK) | digit
                        f -= digit
                        assert 0.0 <= f < 1.0
                        e -= CHUNK

                    # Now |value| = top * 2**e exactly.
                    if e >= 0:
                        n = top << e
                        d = 1
                    else:
                        n = top
                        d = 1 << -e
                    if value < 0:
                        n = -n
                    self.n = n
                    self.d = d
                    assert float(n) / float(d) == value
                else:
                    raise TypeError("can't deal with %r" % value)