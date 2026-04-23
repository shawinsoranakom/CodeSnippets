def make_allpass(
    frequency: int,
    samplerate: int,
    q_factor: float = 1 / sqrt(2),
) -> IIRFilter:
    w0 = tau * frequency / samplerate
    _sin = sin(w0)
    _cos = cos(w0)
    alpha = _sin / (2 * q_factor)

    b0 = 1 - alpha
    b1 = -2 * _cos
    b2 = 1 + alpha

    filt = IIRFilter(2)
    filt.set_coefficients([b2, b1, b0], [b0, b1, b2])
    return filt
