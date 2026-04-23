def binary_search(
    function: Callable[[float], float],
    target: float,
    lower_bound: float,
    upper_bound: float,
    tolerance:float = 1e-4
) -> float | None:
    lh = lower_bound
    rh = upper_bound
    mh = (lh + rh) / 2
    while abs(rh - lh) > tolerance:
        lx, mx, rx = [function(h) for h in (lh, mh, rh)]
        if lx == target:
            return lx
        if rx == target:
            return rx

        if lx <= target and rx >= target:
            if mx > target:
                rh = mh
            else:
                lh = mh
        elif lx > target and rx < target:
            lh, rh = rh, lh
        else:
            return None
        mh = (lh + rh) / 2
    return mh