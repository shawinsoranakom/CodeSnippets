def spectrogram_batch(
    waveform_list: list[np.ndarray],
    window: np.ndarray,
    frame_length: int,
    hop_length: int,
    fft_length: int | None = None,
    power: float | None = 1.0,
    center: bool = True,
    pad_mode: str = "reflect",
    onesided: bool = True,
    dither: float = 0.0,
    preemphasis: float | None = None,
    mel_filters: np.ndarray | None = None,
    mel_floor: float = 1e-10,
    log_mel: str | None = None,
    reference: float = 1.0,
    min_value: float = 1e-10,
    db_range: float | None = None,
    remove_dc_offset: bool = False,
    dtype: np.dtype = np.float32,
) -> list[np.ndarray]:
    """
    Calculates spectrograms for a list of waveforms using the Short-Time Fourier Transform, optimized for batch processing.
    This function extends the capabilities of the `spectrogram` function to handle multiple waveforms efficiently by leveraging broadcasting.

    It supports generating various types of spectrograms:

        - amplitude spectrogram (`power = 1.0`)
        - power spectrogram (`power = 2.0`)
        - complex-valued spectrogram (`power = None`)
        - log spectrogram (use `log_mel` argument)
        - mel spectrogram (provide `mel_filters`)
        - log-mel spectrogram (provide `mel_filters` and `log_mel`)

    How this works:

        1. The input waveform is split into frames of size `frame_length` that are partially overlapping by `frame_length
            - hop_length` samples.
        2. Each frame is multiplied by the window and placed into a buffer of size `fft_length`.
        3. The DFT is taken of each windowed frame.
        4. The results are stacked into a spectrogram.

    We make a distinction between the following "blocks" of sample data, each of which may have a different lengths:

      - The analysis frame. This is the size of the time slices that the input waveform is split into.
      - The window. Each analysis frame is multiplied by the window to avoid spectral leakage.
      - The FFT input buffer. The length of this determines how many frequency bins are in the spectrogram.

    In this implementation, the window is assumed to be zero-padded to have the same size as the analysis frame. A
    padded window can be obtained from `window_function()`. The FFT input buffer may be larger than the analysis frame,
    typically the next power of two.

    Note: This function is designed for efficient batch processing of multiple waveforms but retains compatibility with individual waveform processing methods like `librosa.stft`.

    Args:
        waveform_list (`list[np.ndarray]` with arrays of shape `(length,)`):
            The list of input waveforms, each a single-channel (mono) signal.
        window (`np.ndarray` of shape `(frame_length,)`):
            The windowing function to apply, including zero-padding if necessary.
        frame_length (`int`):
            The length of each frame for analysis.
        hop_length (`int`):
            The step size between successive frames.
        fft_length (`int`, *optional*):
            The size of the FFT buffer, defining frequency bin resolution.
        power (`float`, *optional*, defaults to 1.0):
            Determines the type of spectrogram: 1.0 for amplitude, 2.0 for power, None for complex.
        center (`bool`, *optional*, defaults to `True`):
            Whether to center-pad the waveform frames.
        pad_mode (`str`, *optional*, defaults to `"reflect"`):
            The padding strategy when `center` is `True`.
        onesided (`bool`, *optional*, defaults to `True`):
            If True, returns a one-sided spectrogram for real input signals.
        dither (`float`, *optional*, defaults to 0.0):
            Adds dithering. In other words, adds a small Gaussian noise to each frame.
            E.g. use 4.0 to add dithering with a normal distribution centered
            around 0.0 with standard deviation 4.0, 0.0 means no dithering.
        preemphasis (`float`, *optional*):
            Applies a pre-emphasis filter to each frame.
        mel_filters (`np.ndarray`, *optional*):
            Mel filter bank for converting to mel spectrogram.
        mel_floor (`float`, *optional*, defaults to 1e-10):
            Floor value for mel spectrogram to avoid log(0).
        log_mel (`str`, *optional*):
            Specifies log scaling strategy; options are None, "log", "log10", "dB".
        reference (`float`, *optional*, defaults to 1.0):
            Reference value for dB conversion in log_mel.
        min_value (`float`, *optional*, defaults to 1e-10):
            Minimum floor value for log scale conversions.
        db_range (`float`, *optional*):
            Dynamic range for dB scale spectrograms.
        remove_dc_offset (`bool`, *optional*):
            Whether to remove the DC offset from each frame.
        dtype (`np.dtype`, *optional*, defaults to `np.float32`):
            Data type of the output spectrogram.

    Returns:
        list[`np.ndarray`]: A list of spectrogram arrays, one for each input waveform.
    """
    window_length = len(window)

    if fft_length is None:
        fft_length = frame_length

    if frame_length > fft_length:
        raise ValueError(f"frame_length ({frame_length}) may not be larger than fft_length ({fft_length})")

    if window_length != frame_length:
        raise ValueError(f"Length of the window ({window_length}) must equal frame_length ({frame_length})")

    if hop_length <= 0:
        raise ValueError("hop_length must be greater than zero")

    # Check the dimensions of the waveform , and if waveform is complex
    for waveform in waveform_list:
        if waveform.ndim != 1:
            raise ValueError(f"Input waveform must have only one dimension, shape is {waveform.shape}")
        if np.iscomplexobj(waveform):
            raise ValueError("Complex-valued input waveforms are not currently supported")
    # Center pad the waveform
    if center:
        padding = [(int(frame_length // 2), int(frame_length // 2))]
        waveform_list = [
            np.pad(
                waveform,
                padding,
                mode=pad_mode,
            )
            for waveform in waveform_list
        ]
    original_waveform_lengths = [
        len(waveform) for waveform in waveform_list
    ]  # these lengths will be used to remove padding later

    # Batch pad the waveform
    max_length = max(original_waveform_lengths)
    padded_waveform_batch = np.array(
        [
            np.pad(waveform, (0, max_length - len(waveform)), mode="constant", constant_values=0)
            for waveform in waveform_list
        ],
        dtype=dtype,
    )

    # Promote to float64, since np.fft uses float64 internally
    padded_waveform_batch = padded_waveform_batch.astype(np.float64)
    window = window.astype(np.float64)

    # Split waveform into frames of frame_length size
    num_frames = int(1 + np.floor((padded_waveform_batch.shape[1] - frame_length) / hop_length))
    # these lengths will be used to remove padding later
    true_num_frames = [int(1 + np.floor((length - frame_length) / hop_length)) for length in original_waveform_lengths]
    num_batches = padded_waveform_batch.shape[0]

    num_frequency_bins = (fft_length // 2) + 1 if onesided else fft_length
    spectrogram = np.empty((num_batches, num_frames, num_frequency_bins), dtype=np.complex64)

    # rfft is faster than fft
    fft_func = np.fft.rfft if onesided else np.fft.fft
    buffer = np.zeros((num_batches, fft_length))

    for frame_idx in range(num_frames):
        timestep = frame_idx * hop_length
        buffer[:, :frame_length] = padded_waveform_batch[:, timestep : timestep + frame_length]

        if dither != 0.0:
            buffer[:, :frame_length] += dither * np.random.randn(*buffer[:, :frame_length].shape)

        if remove_dc_offset:
            buffer[:, :frame_length] -= buffer[:, :frame_length].mean(axis=1, keepdims=True)

        if preemphasis is not None:
            buffer[:, 1:frame_length] -= preemphasis * buffer[:, : frame_length - 1]
            buffer[:, 0] *= 1 - preemphasis

        buffer[:, :frame_length] *= window

        spectrogram[:, frame_idx] = fft_func(buffer)

    # Note: ** is much faster than np.power
    if power is not None:
        spectrogram = np.abs(spectrogram, dtype=np.float64) ** power

    # Apply mel filters if provided
    if mel_filters is not None:
        result = np.tensordot(spectrogram, mel_filters.T, axes=([2], [1]))
        spectrogram = np.maximum(mel_floor, result)

    # Convert to log scale if specified
    if power is not None and log_mel is not None:
        if log_mel == "log":
            spectrogram = np.log(spectrogram)
        elif log_mel == "log10":
            spectrogram = np.log10(spectrogram)
        elif log_mel == "dB":
            if power == 1.0:
                spectrogram = amplitude_to_db_batch(spectrogram, reference, min_value, db_range)
            elif power == 2.0:
                spectrogram = power_to_db_batch(spectrogram, reference, min_value, db_range)
            else:
                raise ValueError(f"Cannot use log_mel option '{log_mel}' with power {power}")
        else:
            raise ValueError(f"Unknown log_mel option: {log_mel}")

        spectrogram = np.asarray(spectrogram, dtype)

    spectrogram_list = [spectrogram[i, : true_num_frames[i], :].T for i in range(len(true_num_frames))]

    return spectrogram_list