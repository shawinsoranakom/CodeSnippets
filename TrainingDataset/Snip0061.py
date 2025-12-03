def make_peak(
    frequency: int,
    samplerate: int,
    gain_db: float,
    q_factor: float = 1 / sqrt(2),
) -> IIRFilter:
    w0 = tau * frequency / samplerate
    _sin = sin(w0)
    _cos = cos(w0)
    alpha = _sin / (2 * q_factor)
    big_a = 10 ** (gain_db / 40)

    b0 = 1 + alpha * big_a
    b1 = -2 * _cos
    b2 = 1 - alpha * big_a
    a0 = 1 + alpha / big_a
    a1 = -2 * _cos
    a2 = 1 - alpha / big_a

    filt = IIRFilter(2)
    filt.set_coefficients([a0, a1, a2], [b0, b1, b2])
    return filt
