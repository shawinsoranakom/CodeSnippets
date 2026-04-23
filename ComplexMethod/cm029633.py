def compute_powers(w, base, more_than, *, need_hi=False, show=False):
    seen = set()
    need = set()
    ws = {w}
    while ws:
        w = ws.pop() # any element is fine to use next
        if w in seen or w <= more_than:
            continue
        seen.add(w)
        lo = w >> 1
        hi = w - lo
        # only _need_ one here; the other may, or may not, be needed
        which = hi if need_hi else lo
        need.add(which)
        ws.add(which)
        if lo != hi:
            ws.add(w - which)

    # `need` is the set of exponents needed. To compute them all
    # efficiently, possibly add other exponents to `extra`. The goal is
    # to ensure that each exponent can be gotten from a smaller one via
    # multiplying by the base, squaring it, or squaring and then
    # multiplying by the base.
    #
    # If need_hi is False, this is already the case (w can always be
    # gotten from w >> 1 via one of the squaring strategies). But we do
    # the work anyway, just in case ;-)
    #
    # Note that speed is irrelevant. These loops are working on little
    # ints (exponents) and go around O(log w) times. The total cost is
    # insignificant compared to just one of the bigint multiplies.
    cands = need.copy()
    extra = set()
    while cands:
        w = max(cands)
        cands.remove(w)
        lo = w >> 1
        if lo > more_than and w-1 not in cands and lo not in cands:
            extra.add(lo)
            cands.add(lo)
    assert need_hi or not extra

    d = {}
    for n in sorted(need | extra):
        lo = n >> 1
        hi = n - lo
        if n-1 in d:
            if show:
                print("* base", end="")
            result = d[n-1] * base # cheap!
        elif lo in d:
            # Multiplying a bigint by itself is about twice as fast
            # in CPython provided it's the same object.
            if show:
                print("square", end="")
            result = d[lo] * d[lo] # same object
            if hi != lo:
                if show:
                    print(" * base", end="")
                assert 2 * lo + 1 == n
                result *= base
        else: # rare
            if show:
                print("pow", end='')
            result = base ** n
        if show:
            print(" at", n, "needed" if n in need else "extra")
        d[n] = result

    assert need <= d.keys()
    if excess := d.keys() - need:
        assert need_hi
        for n in excess:
            del d[n]
    return d