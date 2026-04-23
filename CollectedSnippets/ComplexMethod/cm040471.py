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

    ori_dtype = x.dtype
    x = get_ov_output(x)

    ori_shape = x.shape
    num_dims = len(ori_shape)

    if num_dims > 2:
        flatten_shape = ov_opset.constant([-1, ori_shape[-1]], Type.i32).output(
            0
        )
        x = ov_opset.reshape(x, flatten_shape, False).output(0)

    if center:
        # pad x with reflect mode
        pad_begin = [0] * len(x.shape)
        pad_end = [0] * len(x.shape)
        pad_begin[-1] = fft_length // 2
        pad_end[-1] = fft_length // 2
        pad_begin_node = ov_opset.constant(pad_begin, Type.i32).output(0)
        pad_end_node = ov_opset.constant(pad_end, Type.i32).output(0)
        x = ov_opset.pad(x, pad_begin_node, pad_end_node, "reflect").output(0)

    l_pad = (fft_length - sequence_length) // 2
    r_pad = fft_length - sequence_length - l_pad

    element_type = x.get_element_type()
    if element_type == Type.f64:
        x = ov_opset.convert(x, Type.f32).output(0)
        element_type = Type.f32

    if window is not None:
        if isinstance(window, str):
            win = scipy.signal.get_window(window, sequence_length)
        else:
            win = window
        if len(win.shape) != 1 or win.shape[-1] != sequence_length:
            raise ValueError(
                "The shape of `window` must be equal to [sequence_length]."
                f"Received: window shape={win.shape}"
            )
        win = np.pad(win, [[l_pad, r_pad]])
        win_node = ov_opset.constant(win, element_type).output(0)
    else:
        win = np.ones((sequence_length + l_pad + r_pad))
        win_node = ov_opset.constant(win, element_type).output(0)

    frame_size_node = ov_opset.constant(fft_length, Type.i32).output(0)
    frame_step_node = ov_opset.constant(sequence_stride, Type.i32).output(0)

    stft_node = ov_opset.stft(
        x, win_node, frame_size_node, frame_step_node, transpose_frames=False
    ).output(0)

    out_real = ov_opset.gather(
        stft_node,
        ov_opset.constant(0, Type.i32),
        ov_opset.constant(-1, Type.i32),
    ).output(0)
    out_imag = ov_opset.gather(
        stft_node,
        ov_opset.constant(1, Type.i32),
        ov_opset.constant(-1, Type.i32),
    ).output(0)

    if num_dims > 2:
        target_shape = list(ori_shape[:-1]) + [-1, fft_length // 2 + 1]
        target_shape_node = ov_opset.constant(target_shape, Type.i32).output(0)
        out_real = ov_opset.reshape(out_real, target_shape_node, False).output(
            0
        )
        out_imag = ov_opset.reshape(out_imag, target_shape_node, False).output(
            0
        )

    if ori_dtype == "float64":
        out_real = ov_opset.convert(out_real, Type.f64).output(0)
        out_imag = ov_opset.convert(out_imag, Type.f64).output(0)

    return OpenVINOKerasTensor(out_real), OpenVINOKerasTensor(out_imag)