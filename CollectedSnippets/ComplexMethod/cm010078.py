def calc_conv_nd_return_shape(
    input_tensor: torch.Tensor,
    weight: torch.Tensor,
    stride: list[int] | int,
    padding: list[int] | int,
    dilation: list[int] | int,
    is_transposed: bool,
    groups: int,
    output_padding: list[int] | int | None = None,
):
    def _formula(ln: int, p: int, d: int, k: int, s: int) -> int:
        """
        Formula to apply to calculate the length of some dimension of the output

        See: https://pytorch.org/docs/stable/generated/torch.nn.Conv2d.html

        Args:
            ln: length of the dimension
            p: padding in that dim
            d: dilation in that dim
            k: kernel size in that dim
            s: stride in that dim
        Returns:
            The output length
        """
        return (ln + 2 * p - d * (k - 1) - 1) // s + 1

    def _formula_transposed(ln: int, p: int, d: int, k: int, s: int, op: int) -> int:
        """
        Formula to apply to calculate the length of some dimension of the output
        if transposed convolution is used.
        See: https://pytorch.org/docs/stable/generated/torch.nn.ConvTranspose2d.html

        Args:
            ln: length of the dimension
            p: padding in that dim
            d: dilation in that dim
            k: kernel size in that dim
            s: stride in that dim
            op: output padding in that dim

        Returns:
            The output length
        """
        return (ln - 1) * s - 2 * p + d * (k - 1) + op + 1

    kernel_size = weight.shape[2:]
    dims = input_tensor.shape[2:]
    if is_transposed:
        out_channels = groups * weight.shape[1]
    else:
        out_channels = weight.shape[0]
        torch._check(
            weight.shape[1] * groups == input_tensor.shape[1],
            lambda: "Invalid channel dimensions",
        )

    ret_shape = [input_tensor.shape[0], out_channels]
    if isinstance(stride, IntLike):
        # pyrefly: ignore [bad-assignment]
        stride = [stride] * len(dims)
    elif len(stride) == 1:
        stride = [stride[0]] * len(dims)

    if isinstance(padding, IntLike):
        # pyrefly: ignore [bad-assignment]
        padding = [padding] * len(dims)
    elif len(padding) == 1:
        padding = [padding[0]] * len(dims)

    if isinstance(dilation, IntLike):
        # pyrefly: ignore [bad-assignment]
        dilation = [dilation] * len(dims)
    elif len(dilation) == 1:
        dilation = [dilation[0]] * len(dims)

    output_padding_list: list[int] | None = None
    if output_padding:
        if isinstance(output_padding, IntLike):
            # pyrefly: ignore [bad-assignment]
            output_padding_list = [output_padding] * len(dims)
        elif len(output_padding) == 1:
            output_padding_list = [output_padding[0]] * len(dims)
        else:
            output_padding_list = output_padding

    for i in range(len(dims)):
        # If output_padding is present, we are dealing with a transposed convolution
        if output_padding_list:
            ret_shape.append(
                _formula_transposed(
                    dims[i],
                    # pyrefly: ignore [bad-index]
                    padding[i],
                    # pyrefly: ignore [bad-index, index-error]
                    # pyrefly: ignore [bad-index, index-error]
                    dilation[i],
                    kernel_size[i],
                    # pyrefly: ignore [bad-index, index-error]
                    stride[i],
                    output_padding_list[i],
                )
            )
        else:
            ret_shape.append(
                # pyrefly: ignore [bad-index, index-error]
                _formula(dims[i], padding[i], dilation[i], kernel_size[i], stride[i])
            )
    # NOTE: Backend behavior for zero-sized spatial dimensions is inconsistent.
    # CUDA (cuDNN) handles zero-sized outputs gracefully by short-circuiting,
    # but other backends fail: CPU rejects it, ROCm/miopen returns
    # miopenStatusBadParm, and MPS asserts "Placeholder tensor is empty".
    # We only allow zero-sized outputs on CUDA with cuDNN (not ROCm/HIP).
    from torch._subclasses.fake_tensor import FakeTensor
    from torch.fx.experimental.symbolic_shapes import sym_or

    device = (
        input_tensor.fake_device
        if isinstance(input_tensor, FakeTensor)
        else input_tensor.device
    )

    # ROCm also reports device.type as "cuda", but miopen doesn't support zero-sized outputs
    is_cudnn = device.type == "cuda" and torch.version.hip is None
    if not is_cudnn:
        torch._check(
            sym_or(*[x > 0 for x in ret_shape[2:]]),
            lambda: f"Given input size per channel: {list(dims)}. "
            f"Calculated output size per channel: {ret_shape[2:]}. "
            f"Output size is too small",
        )

    return ret_shape