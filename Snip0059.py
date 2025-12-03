def make_bandpass(
    frequency: int,
    samplerate: int,
    q_factor: float = 1 / sqrt(2),
) -> IIRFilter:
    w0 = tau * frequency / samplerate
    _sin = sin(w0)
    _cos = cos(w0)
    alpha = _sin / (2 * q_factor)

    b0 = _sin / 2
    b1 = 0
    b2 = -b0

    a0 = 1 + alpha
    a1 = -2 * _cos
    a2 = 1 - alpha

    filt = IIRFilter(2)
    filt.set_coefficients([a0, a1, a2], [b0, b1, b2])
    return filt
