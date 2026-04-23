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
    dtype = complex_input.real.dtype
    win = None
    if window is not None:
        if isinstance(window, str):
            if window == "hann":
                win = torch.hann_window(
                    sequence_length,
                    periodic=True,
                    dtype=dtype,
                    device=get_device(),
                )
            else:
                win = torch.hamming_window(
                    sequence_length,
                    periodic=True,
                    dtype=dtype,
                    device=get_device(),
                )
        else:
            win = convert_to_tensor(window, dtype=dtype)
        if len(win.shape) != 1 or win.shape[-1] != sequence_length:
            raise ValueError(
                "The shape of `window` must be equal to [sequence_length]."
                f"Received: window shape={win.shape}"
            )

    if sequence_length == fft_length and center is True and win is not None:
        # can be fallen back to torch.istft
        need_unpack = False
        *batch_shape, num_sequences, fft_unique_bins = complex_input.shape
        if len(complex_input.shape) > 3:
            need_unpack = True
            flat_batchsize = math.prod(batch_shape)
            complex_input = torch.reshape(
                complex_input, (flat_batchsize, num_sequences, fft_unique_bins)
            )
        complex_input = torch.swapaxes(complex_input, -2, -1)
        x = torch.istft(
            complex_input,
            n_fft=fft_length,
            hop_length=sequence_stride,
            win_length=sequence_length,
            window=win,
            center=center,
            length=length,
            return_complex=False,
        )
        if need_unpack:
            samples = x.shape[-1]
            x = torch.reshape(x, (*batch_shape, samples))
        return x

    # custom implementation with irfft and _overlap_sequences
    # references:
    # torch: aten/src/ATen/native/SpectralOps.cpp
    # tf: tf.signal.inverse_stft_window_fn
    x = irfft(x, fft_length)

    expected_output_len = fft_length + sequence_stride * (x.shape[-2] - 1)

    if win is not None:
        l_pad = (fft_length - sequence_length) // 2
        r_pad = fft_length - sequence_length - l_pad
        win = pad(win, [[l_pad, r_pad]], "constant")

        # square and sum
        _sequence_length = sequence_length + l_pad + r_pad
        denom = torch.square(win)
        overlaps = -(-_sequence_length // sequence_stride)
        denom = pad(denom, [(0, overlaps * sequence_stride - _sequence_length)])
        denom = torch.reshape(denom, [overlaps, sequence_stride])
        denom = torch.sum(denom, 0, keepdims=True)
        denom = torch.tile(denom, [overlaps, 1])
        denom = torch.reshape(denom, [overlaps * sequence_stride])
        win = torch.divide(win, denom[:_sequence_length])
        x = torch.multiply(x, win)

    x = _overlap_sequences(x, sequence_stride)

    start = 0 if center is False else fft_length // 2
    if length is not None:
        end = start + length
    elif center is True:
        end = -(fft_length // 2)
    else:
        end = expected_output_len
    return x[..., start:end]