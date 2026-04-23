def stft(
    input: Tensor,
    n_fft: int,
    hop_length: int | None = None,
    win_length: int | None = None,
    window: Tensor | None = None,
    center: bool = True,
    pad_mode: str = "reflect",
    normalized: bool = False,
    onesided: bool | None = None,
    return_complex: bool | None = None,
    align_to_window: bool | None = None,
) -> Tensor:
    torch._check(
        window is None or window.device == input.device,
        lambda: (
            f"stft input and window must be on the same device but got self on {input.device}"
            + f" and window on {window.device}"  # type: ignore[union-attr]
        ),
    )
    torch._check(
        not center or align_to_window is None,
        lambda: "stft only supports align_to_window for center = False.",
    )

    hop_length_ = hop_length if hop_length is not None else n_fft // 4
    win_length_ = win_length if win_length is not None else n_fft

    if return_complex is None:
        return_complex_ = input.is_complex() or (
            window is not None and utils.is_complex_dtype(window.dtype)
        )
        torch._check(
            return_complex_,
            lambda: (
                "stft requires the return_complex parameter be given for real inputs, "
                + "and will further require that return_complex=True in a future PyTorch release."
            ),
        )
    else:
        return_complex_ = return_complex

    torch._check(
        utils.is_float_dtype(input.dtype) or utils.is_complex_dtype(input.dtype),
        lambda: "stft expected a tensor of floating point or complex values",
    )
    torch._check(1 <= input.ndim <= 2, lambda: "stft expected a 1D or 2D tensor")

    original_ndim = input.ndim
    if original_ndim == 1:
        input = input.unsqueeze(0)

    if center:
        extra_dims = 3 - input.ndim
        pad_amount = n_fft // 2
        extended_shape = [*itertools.repeat(1, extra_dims), *input.shape]
        input = aten.pad(input.view(extended_shape), [pad_amount, pad_amount], pad_mode)
        input = input.view(input.size()[extra_dims:])

    length = input.size(1)
    torch._check(
        0 < n_fft <= length,
        lambda: f"stft expected 0 < n_fft <= {length}, but got n_fft={n_fft}",
    )
    torch._check(
        hop_length_ > 0,
        lambda: f"stft expected hop_length > 0 but got hop_length={hop_length_}",
    )
    torch._check(
        0 < win_length_ <= n_fft,
        lambda: f"stft expected 0 < win_length <= n_fft but got win_length={win_length_}",
    )
    torch._check(
        window is None or window.shape == (win_length_,),
        lambda: (
            f"expected a 1D window tensor of size equal to win_length={win_length_}, "
            + f"but got window with size {window.shape}"  # type: ignore[union-attr]
        ),
    )

    if win_length_ < n_fft:
        if window is None:
            window = torch.ones(win_length_, dtype=input.dtype, device=input.device)
        left = (n_fft - win_length_) // 2
        window = aten.constant_pad_nd(window, [left, n_fft - win_length_ - left])

    if not center and align_to_window:
        input_pad_amount = (n_fft - win_length_) // 2
        input = aten.pad(input, [input_pad_amount, input_pad_amount], pad_mode)

    input = input.unfold(dimension=-1, size=n_fft, step=hop_length_)

    if window is not None:
        input = input * window

    complex_fft = utils.is_complex_dtype(input.dtype)
    onesided = onesided if onesided is not None else not complex_fft
    norm = "ortho" if normalized else None
    if onesided:
        torch._check(
            not complex_fft,
            lambda: "Cannot have onesided output if window or input is complex",
        )
        out = torch.fft.rfft(input, dim=-1, norm=norm)
    else:
        out = torch.fft.fft(input, dim=-1, norm=norm)

    out.transpose_(1, 2)

    if original_ndim == 1:
        out = out.squeeze_(0)

    return out if return_complex_ else torch.view_as_real(out)