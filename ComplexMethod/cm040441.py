def _convert_conv_transpose_padding_args_from_keras_to_torch(
    kernel_size, stride, dilation_rate, padding, output_padding
):
    """Convert the padding arguments from Keras to the ones used by Torch.
    Torch starts with an output shape of `(input-1) * stride + kernel_size`,
    then removes `torch_padding` from both sides, and adds
    `torch_output_padding` on the right.
    Because in Torch the output_padding can only be added to the right,
    consistency with Tensorflow is not always possible. In particular this is
    the case when both the Torch padding and output_padding values are
    strictly positive.
    """
    if padding.lower() not in {"valid", "same"}:
        raise ValueError(
            f"The `padding` argument must be one of 'valid', 'same'. "
            f"Received: padding={padding}"
        )
    original_kernel_size = kernel_size
    kernel_size = (kernel_size - 1) * dilation_rate + 1

    if padding.lower() == "valid":
        # If output_padding is None, we fill it so that the shape of the output
        # is `(i-1)*s + max(k, s)`
        output_padding = (
            max(kernel_size, stride) - kernel_size
            if output_padding is None
            else output_padding
        )
        torch_padding = 0
        torch_output_padding = output_padding

    else:
        # When output_padding is None, we want the shape of the output to be
        # `input * s`, otherwise we use the value provided.
        output_padding = (
            stride - kernel_size % 2
            if output_padding is None
            else output_padding
        )
        torch_padding = max(
            -((kernel_size % 2 - kernel_size + output_padding) // 2), 0
        )
        torch_output_padding = (
            2 * torch_padding + kernel_size % 2 - kernel_size + output_padding
        )

    if torch_padding > 0 and torch_output_padding > 0:
        warnings.warn(
            f"You might experience inconsistencies across backends when "
            f"calling conv transpose with kernel_size={original_kernel_size}, "
            f"stride={stride}, dilation_rate={dilation_rate}, "
            f"padding={padding}, output_padding={output_padding}."
        )

    if torch_output_padding >= stride:
        warnings.warn(
            f"Torch backend requires output_padding < stride. "
            f"Clamping output_padding {torch_output_padding} -> {stride - 1} "
            f"for stride {stride}.",
            UserWarning,
        )
        torch_output_padding = stride - 1

    return torch_padding, torch_output_padding