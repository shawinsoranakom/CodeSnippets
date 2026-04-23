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

    if window is not None:
        if isinstance(window, str):
            if window == "hann":
                win = torch.hann_window(
                    sequence_length,
                    periodic=True,
                    dtype=x.dtype,
                    device=get_device(),
                )
            else:
                win = torch.hamming_window(
                    sequence_length,
                    periodic=True,
                    dtype=x.dtype,
                    device=get_device(),
                )
        else:
            win = convert_to_tensor(window, dtype=x.dtype)
        if len(win.shape) != 1 or win.shape[-1] != sequence_length:
            raise ValueError(
                "The shape of `window` must be equal to [sequence_length]."
                f"Received: window shape={win.shape}"
            )
    else:
        win = torch.ones((sequence_length,), dtype=x.dtype, device=get_device())

    need_unpack = False
    *batch_shape, samples = x.shape
    if len(x.shape) > 2:
        need_unpack = True
        flat_batchsize = math.prod(batch_shape)
        x = torch.reshape(x, (flat_batchsize, samples))

    x = torch.stft(
        x,
        n_fft=fft_length,
        hop_length=sequence_stride,
        win_length=sequence_length,
        window=win,
        center=center,
        return_complex=True,
    )
    if need_unpack:
        fft_unique_bins, num_sequences = x.shape[-2:]
        x = torch.reshape(x, (*batch_shape, fft_unique_bins, num_sequences))

    x = torch.swapaxes(x, -2, -1)
    return x.real, x.imag