def stft(
    x, sequence_length, sequence_stride, fft_length, window="hann", center=True
):
    if standardize_dtype(x.dtype) not in {"float32", "float64"}:
        raise TypeError(
            "Invalid input type. Expected `float32` or `float64`. "
            f"Received: input type={x.dtype}"
        )
    if fft_length < sequence_length:
        raise ValueError(
            "`fft_length` must equal or larger than `sequence_length`. "
            f"Received: sequence_length={sequence_length}, "
            f"fft_length={fft_length}"
        )
    if isinstance(window, str):
        if window not in {"hann", "hamming"}:
            raise ValueError(
                "If a string is passed to `window`, it must be one of "
                f'`"hann"`, `"hamming"`. Received: window={window}'
            )
    x = convert_to_tensor(x)

    if center:
        pad_width = [(0, 0) for _ in range(len(x.shape))]
        pad_width[-1] = (fft_length // 2, fft_length // 2)
        x = tf.pad(x, pad_width, mode="reflect")

    l_pad = (fft_length - sequence_length) // 2
    r_pad = fft_length - sequence_length - l_pad

    if window is not None:
        if isinstance(window, str):
            if window == "hann":
                win_array = tf.signal.hann_window(
                    sequence_length, periodic=True, dtype=x.dtype
                )
            else:
                win_array = tf.signal.hamming_window(
                    sequence_length, periodic=True, dtype=x.dtype
                )
        else:
            win_array = convert_to_tensor(window, dtype=x.dtype)
        if len(win_array.shape) != 1 or win_array.shape[-1] != sequence_length:
            raise ValueError(
                "The shape of `window` must be equal to [sequence_length]."
                f"Received: window shape={win_array.shape}"
            )
        win_array = tf.pad(win_array, [[l_pad, r_pad]])

        def win(frame_step, dtype):
            return win_array

    else:
        win = None

    result = tf.signal.stft(
        x,
        frame_length=(sequence_length + l_pad + r_pad),
        frame_step=sequence_stride,
        fft_length=fft_length,
        window_fn=win,
    )
    return tf.math.real(result), tf.math.imag(result)