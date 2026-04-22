def note(freq, length, amp, rate):
    t = np.linspace(0, length, length * rate)
    data = np.sin(2 * np.pi * freq * t) * amp
    return data.astype(np.int16)