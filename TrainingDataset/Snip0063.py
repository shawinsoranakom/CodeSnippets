def make_highshelf(
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
    pmc = (big_a + 1) - (big_a - 1) * _cos
    ppmc = (big_a + 1) + (big_a - 1) * _cos
    mpc = (big_a - 1) - (big_a + 1) * _cos
    pmpc = (big_a - 1) + (big_a + 1) * _cos
    aa2 = 2 * sqrt(big_a) * alpha

    b0 = big_a * (ppmc + aa2)
    b1 = -2 * big_a * pmpc
    b2 = big_a * (ppmc - aa2)
    a0 = pmc + aa2
    a1 = 2 * mpc
    a2 = pmc - aa2

    filt = IIRFilter(2)
    filt.set_coefficients([a0, a1, a2], [b0, b1, b2])
    return filt
