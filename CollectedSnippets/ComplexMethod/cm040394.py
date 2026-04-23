def istft(
    x,
    sequence_length,
    sequence_stride,
    fft_length,
    length=None,
    window="hann",
    center=True,
):
    complex_input = _get_complex_tensor_from_tuple(x)
    dtype = tf.math.real(complex_input).dtype

    expected_output_len = fft_length + sequence_stride * (
        tf.shape(complex_input)[-2] - 1
    )
    l_pad = (fft_length - sequence_length) // 2
    r_pad = fft_length - sequence_length - l_pad

    if window is not None:
        if isinstance(window, str):
            if window == "hann":
                win_array = tf.signal.hann_window(
                    sequence_length, periodic=True, dtype=dtype
                )
            else:
                win_array = tf.signal.hamming_window(
                    sequence_length, periodic=True, dtype=dtype
                )
        else:
            win_array = convert_to_tensor(window, dtype=dtype)
        if len(win_array.shape) != 1 or win_array.shape[-1] != sequence_length:
            raise ValueError(
                "The shape of `window` must be equal to [sequence_length]."
                f"Received: window shape={win_array.shape}"
            )
        win_array = tf.pad(win_array, [[l_pad, r_pad]])
        win = tf.signal.inverse_stft_window_fn(
            sequence_stride, lambda frame_step, dtype: win_array
        )
    else:
        win = None

    x = tf.signal.inverse_stft(
        complex_input,
        frame_length=(sequence_length + l_pad + r_pad),
        frame_step=sequence_stride,
        fft_length=fft_length,
        window_fn=win,
    )

    start = 0 if center is False else fft_length // 2
    if length is not None:
        end = start + length
    elif center is True:
        end = -(fft_length // 2)
    else:
        end = expected_output_len
    return x[..., start:end]