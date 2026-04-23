def istft(
    x,
    sequence_length,
    sequence_stride,
    fft_length,
    length=None,
    window="hann",
    center=True,
):
    x = _get_complex_tensor_from_tuple(x)
    dtype = jnp.real(x).dtype

    if len(x.shape) < 2:
        raise ValueError(
            f"Input `x` must have at least 2 dimensions. "
            f"Received shape: {x.shape}"
        )

    expected_output_len = fft_length + sequence_stride * (x.shape[-2] - 1)
    l_pad = (fft_length - sequence_length) // 2
    r_pad = fft_length - sequence_length - l_pad

    if window is not None:
        if isinstance(window, str):
            win = convert_to_tensor(
                scipy.signal.get_window(window, sequence_length), dtype=dtype
            )
        else:
            win = convert_to_tensor(window, dtype=dtype)
        if len(win.shape) != 1 or win.shape[-1] != sequence_length:
            raise ValueError(
                "The shape of `window` must be equal to [sequence_length]."
                f"Received: window shape={win.shape}"
            )
        win = jnp.pad(win, [[l_pad, r_pad]])
    else:
        win = jnp.ones((sequence_length + l_pad + r_pad), dtype=dtype)

    x = jax.scipy.signal.istft(
        x,
        fs=1.0,
        window=win,
        nperseg=(sequence_length + l_pad + r_pad),
        noverlap=(sequence_length + l_pad + r_pad - sequence_stride),
        nfft=fft_length,
        boundary=False,
        time_axis=-2,
        freq_axis=-1,
    )[-1]

    # scale
    x = x / win.sum() if window is not None else x / sequence_stride

    start = 0 if center is False else fft_length // 2
    if length is not None:
        end = start + length
    elif center is True:
        end = -(fft_length // 2)
    else:
        end = expected_output_len
    return x[..., start:end]