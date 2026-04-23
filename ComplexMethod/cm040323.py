def lstm(
    inputs,
    initial_state_h,
    initial_state_c,
    mask,
    kernel,
    recurrent_kernel,
    bias,
    activation,
    recurrent_activation,
    return_sequences=False,
    go_backwards=False,
    unroll=False,
    batch_first=True,
):
    # Masking is not supported by either the cuDNN or fallback path;
    # fall back to the generic RNN loop before doing any work.
    if mask is not None:
        raise NotImplementedError

    # Get device from inputs
    device = get_device()

    # Convert to torch tensors (convert_to_tensor unwraps Variables)
    kernel = convert_to_tensor(kernel)
    recurrent_kernel = convert_to_tensor(recurrent_kernel)
    if bias is not None:
        bias = convert_to_tensor(bias)

    # Cast inputs/states to the kernel's dtype so integer inputs are promoted
    # to float and mixed-precision dtypes (e.g. float16) are respected.
    compute_dtype = kernel.dtype
    inputs = convert_to_tensor(inputs).to(compute_dtype)
    initial_state_h = convert_to_tensor(initial_state_h).to(compute_dtype)
    initial_state_c = convert_to_tensor(initial_state_c).to(compute_dtype)

    # Preprocess for go_backwards by flipping the sequence
    if go_backwards:
        seq_dim = 1 if batch_first else 0
        inputs = torch.flip(inputs, dims=[seq_dim])

    # Move all tensors to the same device
    inputs = inputs.to(device)
    initial_state_h = initial_state_h.to(device)
    initial_state_c = initial_state_c.to(device)

    cudnn_supported = cudnn_ok(
        activation,
        recurrent_activation,
        unroll,
        use_bias=bias is not None,
    )

    if cudnn_supported:
        cudnn_inputs = inputs
        if not batch_first:
            cudnn_inputs = inputs.permute(1, 0, 2)
        try:
            last_output, outputs, states = _cudnn_lstm(
                cudnn_inputs,
                initial_state_h,
                initial_state_c,
                kernel,
                recurrent_kernel,
                bias,
                return_sequences=return_sequences,
                device=device,
            )
            if not batch_first:
                outputs = outputs.permute(1, 0, 2)
            return last_output, outputs, states
        except Exception:
            pass

    return _fallback_lstm(
        inputs,
        initial_state_h,
        initial_state_c,
        kernel,
        recurrent_kernel,
        bias,
        activation,
        recurrent_activation,
        return_sequences,
        batch_first,
    )