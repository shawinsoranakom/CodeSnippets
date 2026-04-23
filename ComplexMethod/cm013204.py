def conv_transpose_ref(input, weight, bias, stride=1, padding=0,
                       output_padding=0, dilation=1, groups=1,
                       fn=None):
    # Derivative of `conv` is `conv_transpose`.
    # To verify the correctness of `conv_transpose`,
    # we rely `torch.nn.grad` implementation (which is tested in test_nn.py)
    # for floating dtypes.

    if fn is None:
        raise AssertionError("Expected fn to not be None")

    grad_fn_map = {torch.nn.functional.conv_transpose1d: torch.nn.grad.conv1d_input,
                   torch.nn.functional.conv_transpose2d: torch.nn.grad.conv2d_input,
                   torch.nn.functional.conv_transpose3d: torch.nn.grad.conv3d_input}
    batched_dim_map = {torch.nn.functional.conv_transpose1d: 3,
                       torch.nn.functional.conv_transpose2d: 4,
                       torch.nn.functional.conv_transpose3d: 5}

    # Input for `ref` is ndarray.
    input, weight = torch.from_numpy(input), torch.from_numpy(weight)

    is_batched = len(input.shape) == batched_dim_map[fn]
    if not is_batched:
        input = input.unsqueeze(0)

    if bias is not None:
        bias = torch.from_numpy(bias)
        unsqueeze_dims = input.ndim - 2
        for _ in range(unsqueeze_dims):
            bias = bias.unsqueeze(1)

    grad_output = input
    # Get the input shape for grad_fn.
    conv_transpose_output = fn(grad_output.to('meta'), weight.to('meta'), None,
                               stride=stride, padding=padding, output_padding=output_padding,
                               groups=groups, dilation=dilation)
    input_size = conv_transpose_output.shape

    grad_fn = grad_fn_map[fn]
    if weight.dtype.is_complex:
        out = complex_conv(grad_fn, input_size, weight, grad_output, stride, padding, dilation, groups)
    else:  # Floating
        out = grad_fn(input_size, weight, grad_output, stride, padding, dilation, groups)

    if bias is not None:
        out = out + bias

    return out.squeeze(0) if not is_batched else out