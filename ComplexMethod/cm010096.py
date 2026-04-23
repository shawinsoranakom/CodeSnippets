def _constant_pad_nd_meta(input, pad, value=0):
    # same checks as decomposition in torch/_refs/__init__.py:constant_pad_nd()
    torch._check(
        len(pad) % 2 == 0,
        lambda: f"Length of pad must be even but instead it equals {len(pad)}",
    )

    input_sizes = input.shape
    l_inp = len(input_sizes)
    l_pad = len(pad) // 2
    l_diff = l_inp - l_pad

    torch._check(
        l_inp >= l_pad,
        lambda: "Length of pad should be no more than twice the number of "
        f"dimensions of the input. Pad length is {len(pad)} while the input has "
        f"{l_inp} dimensions.",
    )

    if all(isinstance(p, utils.IntWithoutSymInt) and p <= 0 for p in pad):
        c_input = input
        for i in range(l_diff, l_inp):
            pad_idx = 2 * (l_inp - i - 1)
            if pad[pad_idx] < 0:
                c_input = c_input.narrow(
                    i, -pad[pad_idx], c_input.shape[i] + pad[pad_idx]
                )

            if pad[pad_idx + 1] < 0:
                c_input = c_input.narrow(i, 0, c_input.shape[i] + pad[pad_idx + 1])

        return c_input.clone()

    new_shape = list(input_sizes[:l_diff])
    for i in range(l_pad):
        pad_idx = len(pad) - ((i + 1) * 2)
        new_dim = input_sizes[l_diff + i] + pad[pad_idx] + pad[pad_idx + 1]
        torch._check(
            new_dim >= 0,
            lambda: f"The input size {input_sizes[l_diff + i]}, plus negative padding "
            f"{pad[pad_idx]} and {pad[pad_idx + 1]} resulted in a negative output size, "
            f"which is invalid. Check dimension {l_diff + i} of your input.",
        )
        new_shape.append(new_dim)

    return torch.empty(
        new_shape,
        dtype=input.dtype,
        device=input.device,
        requires_grad=input.requires_grad,
        memory_format=suggest_memory_format(input),
    )