def istft(
    x,
    sequence_length,
    sequence_stride,
    fft_length,
    length=None,
    window="hann",
    center=True,
):
    if isinstance(window, str):
        if window not in {"hann", "hamming"}:
            raise ValueError(
                "If a string is passed to `window`, it must be one of "
                f'`"hann"`, `"hamming"`. Received: window={window}'
            )

    ori_dtype = x[0].dtype

    x0 = get_ov_output(x[0])
    ori_partial_shape = x0.get_partial_shape()
    num_dims = ori_partial_shape.rank.get_length()
    ori_shape_list = [
        None if dim.is_dynamic else dim.get_length()
        for dim in ori_partial_shape
    ]

    l_pad = (fft_length - sequence_length) // 2
    r_pad = fft_length - sequence_length - l_pad

    if window is not None:
        if isinstance(window, str):
            win = scipy.signal.get_window(window, sequence_length)
        else:
            win = np.asarray(window, dtype=np.float64)
        if len(win.shape) != 1 or win.shape[-1] != sequence_length:
            raise ValueError(
                "The shape of `window` must be equal to [sequence_length]."
                f"Received: window shape={win.shape}"
            )
        win = np.pad(win, [[l_pad, r_pad]])

        denom = np.square(win)
        overlaps = -(-fft_length // sequence_stride)
        denom = np.pad(denom, [(0, overlaps * sequence_stride - fft_length)])
        denom = denom.reshape([overlaps, sequence_stride])
        denom = denom.sum(axis=0, keepdims=True)
        denom = np.tile(denom, [overlaps, 1])
        denom = denom.reshape([overlaps * sequence_stride])
        win = win / denom[:fft_length]
    else:
        win = None

    frames = irfft(x, fft_length)
    frames = get_ov_output(frames)

    element_type = frames.get_element_type()
    if element_type == Type.f64:
        frames = ov_opset.convert(frames, Type.f32).output(0)
        element_type = Type.f32

    if win is not None:
        win_node = ov_opset.constant(win.astype(np.float32), Type.f32).output(0)
        if element_type != Type.f32:
            win_node = ov_opset.convert(win_node, element_type).output(0)
        frames = ov_opset.multiply(frames, win_node).output(0)

    if num_dims == 2:
        frames = ov_opset.unsqueeze(
            frames, ov_opset.constant(0, Type.i32)
        ).output(0)
    elif num_dims > 2:
        frames_shp = ov_opset.shape_of(frames, output_type=Type.i32).output(0)
        num_seq_node = ov_opset.gather(
            frames_shp,
            ov_opset.constant(num_dims - 2, Type.i32),
            ov_opset.constant(0, Type.i32),
        ).output(0)
        flatten_shp = ov_opset.concat(
            [
                ov_opset.constant([-1], Type.i32).output(0),
                ov_opset.unsqueeze(
                    num_seq_node, ov_opset.constant(0, Type.i32)
                ).output(0),
                ov_opset.constant([fft_length], Type.i32).output(0),
            ],
            0,
        ).output(0)
        frames = ov_opset.reshape(frames, flatten_shp, False).output(0)

    frames, output_size = _overlap_sequences_ov(
        frames, sequence_stride, fft_length
    )

    start_val = fft_length // 2 if center else 0

    if length is not None:
        frames = ov_opset.slice(
            frames,
            ov_opset.constant([start_val], Type.i32).output(0),
            ov_opset.constant([start_val + length], Type.i32).output(0),
            ov_opset.constant([1], Type.i32).output(0),
            ov_opset.constant([1], Type.i32).output(0),
        ).output(0)
    else:
        if start_val > 0:
            frames = ov_opset.slice(
                frames,
                ov_opset.constant([start_val], Type.i32).output(0),
                ov_opset.constant([INT32_MAX], Type.i32).output(0),
                ov_opset.constant([1], Type.i32).output(0),
                ov_opset.constant([1], Type.i32).output(0),
            ).output(0)
        if center:
            cur_len = ov_opset.gather(
                ov_opset.shape_of(frames, output_type=Type.i32).output(0),
                ov_opset.constant(1, Type.i32),
                ov_opset.constant(0, Type.i32),
            ).output(0)
            end_node = ov_opset.subtract(
                cur_len,
                ov_opset.constant(fft_length // 2, Type.i32),
            ).output(0)
            frames = ov_opset.slice(
                frames,
                ov_opset.constant([0], Type.i32).output(0),
                ov_opset.unsqueeze(
                    end_node, ov_opset.constant(0, Type.i32)
                ).output(0),
                ov_opset.constant([1], Type.i32).output(0),
                ov_opset.constant([1], Type.i32).output(0),
            ).output(0)

    if num_dims == 2:
        frames = ov_opset.squeeze(
            frames, ov_opset.constant([0], Type.i32)
        ).output(0)
    elif num_dims > 2:
        batch_dims = ori_shape_list[:-2]
        target_shape = [d if d is not None else -1 for d in batch_dims] + [-1]
        target_shape_node = ov_opset.constant(target_shape, Type.i32).output(0)
        frames = ov_opset.reshape(frames, target_shape_node, False).output(0)

    if ori_dtype == "float64":
        frames = ov_opset.convert(frames, Type.f64).output(0)

    return OpenVINOKerasTensor(frames)