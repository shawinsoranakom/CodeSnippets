def show_phase_response(filter_type: FilterType, samplerate: int) -> None:

    size = 512
    inputs = [1] + [0] * (size - 1)
    outputs = [filter_type.process(item) for item in inputs]

    filler = [0] * (samplerate - size) 
    outputs += filler
    fft_out = np.angle(np.fft.fft(outputs))

    plt.xlim(24, samplerate / 2 - 1)
    plt.xlabel("Frequency (Hz)")
    plt.xscale("log")

    plt.ylim(-2 * pi, 2 * pi)
    plt.ylabel("Phase shift (Radians)")
    plt.plot(np.unwrap(fft_out, -2 * pi))
    plt.show()
