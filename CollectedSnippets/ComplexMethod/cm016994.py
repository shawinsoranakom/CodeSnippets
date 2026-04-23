def _assert_ratio_bounds(
    ar: float,
    *,
    min_ratio: tuple[float, float] | None = None,
    max_ratio: tuple[float, float] | None = None,
    strict: bool = True,
) -> None:
    """Validate a numeric aspect ratio against optional min/max ratio bounds."""
    lo = _ratio_from_tuple(min_ratio) if min_ratio is not None else None
    hi = _ratio_from_tuple(max_ratio) if max_ratio is not None else None

    if lo is not None and hi is not None and lo > hi:
        lo, hi = hi, lo  # normalize order if caller swapped them

    if lo is not None:
        if (ar <= lo) if strict else (ar < lo):
            op = "<" if strict else "≤"
            raise ValueError(f"Aspect ratio `{ar:.2g}` must be {op} {lo:.2g}.")
    if hi is not None:
        if (ar >= hi) if strict else (ar > hi):
            op = "<" if strict else "≤"
            raise ValueError(f"Aspect ratio `{ar:.2g}` must be {op} {hi:.2g}.")