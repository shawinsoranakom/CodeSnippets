def set_correction(
    unbiased: bool | None = None,
    correction: NumberType | None = None,
) -> float:
    if correction is not None and unbiased is not None:
        raise RuntimeError("cannot specify both correction and unbiased arguments")
    elif correction is None and unbiased is None:
        correction = 1.0
    elif correction is None and unbiased is not None:
        correction = 0.0 if unbiased is False else 1.0
    # NB: we don't actually support symint here, but it's harmless to accept
    if not isinstance(correction, (IntLike, FloatLike)):
        raise ValueError("correction argument should be integer or float")
    return sym_float(correction)