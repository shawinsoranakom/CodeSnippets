def istft(
    input: Tensor,
    n_fft: int,
    hop_length: int | None = None,
    win_length: int | None = None,
    window: Tensor | None = None,
    center: bool = True,
    normalized: bool = False,
    onesided: bool | None = None,
    length: int | None = None,
    return_complex=False,
) -> Tensor:
    torch._check(
        window is None or window.device == input.device,
        lambda: (
            f"istft input and window must be on the same device but got self on {input.device}"
            + f" and window on {window.device}"  # type: ignore[union-attr]
        ),
    )

    hop_length_ = hop_length if hop_length is not None else n_fft // 4
    win_length_ = win_length if win_length is not None else n_fft

    torch._check(
        utils.is_complex_dtype(input.dtype),
        lambda: (
            "istft input and window must be on the same device but got self on "
            + f"{input.device} and window on {window.device}"  # type: ignore[union-attr]
        ),
    )
    n_frames = input.size(-1)
    fft_size = input.size(-2)

    expected_output_signal_len = n_fft + hop_length_ * (n_frames - 1)
    torch._check(input.numel() > 0, lambda: "istft input tensor cannot be empty")
    torch._check(
        2 <= input.ndim <= 3,
        lambda: f"istft expected a tensor with 2 or 3 dimensions, but got {input.ndim}",
    )
    onesided_ = onesided if onesided is not None else fft_size != n_fft

    if onesided_:
        torch._check(
            n_fft // 2 + 1 == fft_size,
            lambda: (
                "istft expected the frequency dimension (3rd to the last) of the input tensor "
                + f"to match n_fft / 2 + 1 when onesided=True, but got {fft_size}"
            ),
        )
    else:
        torch._check(
            n_fft == fft_size,
            lambda: (
                "istft expected the frequency dimension (3rd to the last) of the input tensor "
                + f"to match n_fft when onesided=False, but got {fft_size}",
            ),
        )

    torch._check(
        0 < hop_length_ <= win_length_,
        lambda: "istft expected 0 < hop_length <= win_length",
    )
    torch._check(
        0 < win_length_ <= n_fft, lambda: "istft expected 0 < win_length <= n_fft"
    )
    torch._check(
        window is None or window.shape == (win_length_,),
        lambda: "Invalid window shape. window has to be 1D and length of `win_length`",
    )

    if window is None:
        real_dtype = utils.corresponding_real_dtype(input.dtype)
        window_ = torch.ones(win_length_, dtype=real_dtype, device=input.device)
    else:
        window_ = window

    if win_length_ != n_fft:
        left = (n_fft - win_length_) // 2
        window_ = aten.constant_pad_nd(window_, (left, n_fft - win_length_ - left), 0)

    original_ndim = input.ndim
    if input.ndim == 2:
        input = input.unsqueeze(0)

    input = input.transpose(1, 2)
    norm = "ortho" if normalized else None
    if return_complex:
        torch._check(
            not onesided_,
            lambda: "cannot have onesided output if window or input is complex",
        )
        input = torch.fft.ifft(input, dim=-1, norm=norm)
    else:
        torch._check(
            window is None or not utils.is_complex_dtype(window.dtype),
            lambda: "Complex windows are incompatible with return_complex=False",
        )
        if not onesided_:
            input = input.narrow(dim=-1, start=0, length=n_fft // 2 + 1)
        input = torch.fft.irfft(input, dim=-1, norm=norm)

    if input.size(2) != n_fft:
        raise AssertionError(
            f"Expected input.size(2) == n_fft, got {input.size(2)} != {n_fft}"
        )

    y_tmp = input * window_.view([1, 1, n_fft])
    y = aten.unfold_backward(
        y_tmp,
        input_sizes=(y_tmp.size(0), expected_output_signal_len),
        dim=1,
        size=n_fft,
        step=hop_length_,
    )
    window_envelop = aten.unfold_backward(
        window_.pow(2).expand((1, n_frames, n_fft)),
        input_sizes=(y_tmp.size(0), expected_output_signal_len),
        dim=1,
        size=n_fft,
        step=hop_length_,
    )

    if expected_output_signal_len != y.size(1):
        raise AssertionError(
            f"expected_output_signal_len ({expected_output_signal_len}) != y.size(1) ({y.size(1)})"
        )
    if expected_output_signal_len != window_envelop.size(1):
        raise AssertionError(
            f"expected_output_signal_len ({expected_output_signal_len}) != window_envelop.size(1) ({window_envelop.size(1)})"
        )

    start = n_fft // 2 if center else 0
    if length is not None:
        end = start + length
    elif center:
        end = expected_output_signal_len - n_fft // 2
    else:
        end = expected_output_signal_len

    length = max(0, end - start)
    y = y.narrow(dim=1, start=start, length=length)
    window_envelop = window_envelop.narrow(dim=1, start=start, length=length)

    y = y / window_envelop
    if original_ndim == 2:
        y = y.squeeze(0)

    if end > expected_output_signal_len:
        warnings.warn(
            "The length of signal is shorter than the length parameter. Result is being "
            + "padded with zeros in the tail. Please check your center and hop_length settings",
            stacklevel=2,
        )
        y = aten.constant_pad_nd(y, (0, end - expected_output_signal_len), 0)
    return y