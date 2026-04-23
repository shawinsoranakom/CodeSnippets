def max_pool2d_with_indices_backward(
    grad_output: Tensor,
    self: Tensor,
    kernel_size,
    stride,
    padding,
    dilation,
    ceil_mode: bool,
    indices: Tensor,
):
    """
    Decomposition of max_pool2d_with_indices_backward using scatter_add.

    This replaces the native implementation with a high-level decomposition
    that uses scatter_add for gradient accumulation. The scatter-based approach
    provides automatic optimization opportunities for Inductor and handles all
    pooling configurations without requiring specialized fallback paths.

    Algorithm:
        For each output gradient position, use the corresponding index from the
        forward pass to scatter the gradient to the input position. When multiple
        output positions select the same input position as max, scatter_add
        automatically accumulates their gradients.

    Complexity: O(B * C * H_out * W_out)
        Independent of kernel size, unlike traditional O(B * C * H_in * W_in * K²)
        approaches that iterate over input positions and kernel windows.

    Known Limitations:
        - FP16/BF16: Uses FP32 accumulation internally to preserve precision when
          many gradients accumulate to the same position (overlapping pooling windows).
          This adds slight overhead but ensures numerical stability.
        - Deterministic mode: Falls back to native implementation to ensure
          consistent results across runs

    Args:
        grad_output: Gradient w.r.t. pooling output [B, C, H_out, W_out]
        self: Original input tensor (for shape) [B, C, H_in, W_in]
        kernel_size: Pooling kernel size
        stride: Pooling stride
        padding: Pooling padding
        dilation: Pooling dilation
        ceil_mode: Whether to use ceil for output size calculation
        indices: Indices from forward pass (per-channel linear positions)

    Returns:
        Gradient w.r.t. input [B, C, H_in, W_in]
    """
    # Use native kernel in deterministic mode
    if torch.are_deterministic_algorithms_enabled():
        return NotImplemented

    # MPS: Use native kernel. scatter_add has correctness issues on macOS 14
    # (#163327) and numerical differences on macOS 15+.
    if grad_output.device.type == "mps":
        return NotImplemented

    # Get spatial dimensions
    in_height = self.size(-2)
    in_width = self.size(-1)
    out_height = grad_output.size(-2)
    out_width = grad_output.size(-1)

    # Handle both 3D (C, H, W) and 4D (B, C, H, W) cases by treating 3D as 4D
    is_batched = self.dim() == 4
    if not is_batched:
        self = self.unsqueeze(0)
        grad_output = grad_output.unsqueeze(0)
        indices = indices.unsqueeze(0)

    batch_size = self.size(0)
    channels = self.size(1)

    # For FP16/BF16, use FP32 accumulation to avoid precision loss
    # This is critical when many gradients accumulate to the same position
    # (overlapping pooling windows with large kernels or stride < kernel_size)
    use_fp32_accum = grad_output.dtype in (torch.float16, torch.bfloat16)
    accum_dtype = torch.float32 if use_fp32_accum else grad_output.dtype

    # Create grad_input with correct accumulation dtype from the start
    grad_input_flat = torch.zeros(
        batch_size * channels,
        in_height * in_width,
        dtype=accum_dtype,
        device=grad_output.device,
    )

    # Reshape grad_output and indices to (B*C, H_out*W_out)
    grad_output_flat = grad_output.reshape(
        batch_size * channels, out_height * out_width
    )
    indices_flat = indices.reshape(batch_size * channels, out_height * out_width)

    # Convert grad_output to accumulation dtype if needed
    if use_fp32_accum:
        grad_output_flat = grad_output_flat.to(torch.float32)

    # Scatter gradients to input positions
    grad_input_flat = grad_input_flat.scatter_add(1, indices_flat, grad_output_flat)

    # Reshape back to original input shape
    grad_input = grad_input_flat.reshape(batch_size, channels, in_height, in_width)

    # Convert back to original dtype if we used FP32 accumulation
    if use_fp32_accum:
        grad_input = grad_input.to(grad_output.dtype)

    # Preserve memory format from input (channels_last vs channels_first)
    memory_format = utils.suggest_memory_format(self)
    grad_input = grad_input.contiguous(memory_format=memory_format)

    # Remove batch dimension for 3D case
    if not is_batched:
        grad_input = grad_input.squeeze(0)

    return grad_input