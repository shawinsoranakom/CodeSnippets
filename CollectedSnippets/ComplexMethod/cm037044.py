def scaled_fp4_quant(
    input: torch.Tensor,
    input_global_scale: torch.Tensor,
    is_sf_swizzled_layout: bool = True,
    backend: str = "none",
) -> tuple[torch.Tensor, torch.Tensor]:
    """
    Quantize input tensor to FP4 and return quantized tensor and scale.

    This function quantizes the last dimension of the given tensor `input`. For
    every 16 consecutive elements, a single dynamically computed scaling factor
    is shared. This scaling factor is quantized using the `input_global_scale`
    and is stored in a swizzled layout (see
    https://docs.nvidia.com/cuda/parallel-thread-execution/#tcgen05-mma-scale-factor-b-layout-4x).

    Args:
        input: The input tensor to be quantized to FP4
        input_global_scale: A scalar scaling factor for the entire tensor.
        use_8x4_sf_layout: Whether to use the 8x4 or 128x4 layout for the scaling

    Returns:
        tuple[torch.Tensor, torch.Tensor]: The output tensor in FP4 but every
            two values are packed into a uint8 and float8_e4m3 scaling factors
            in the sizzled layout.
    """
    assert not current_platform.is_rocm()
    assert input.ndim >= 1, f"input.ndim needs to be >= 1, but got {input.ndim}."
    other_dims = 1 if input.ndim == 1 else -1
    input = input.reshape(other_dims, input.shape[-1])
    m, n = input.shape
    block_size = 16

    assert n % block_size == 0, f"last dim has to be multiple of 16, but got {n}."
    assert input.dtype in (torch.float16, torch.bfloat16), (
        f"input.dtype needs to be fp16 or bf16 but got {input.dtype}."
    )

    use_8x4_sf_layout = True if "trtllm" in backend and m <= 32 else False  # noqa: SIM210

    if use_8x4_sf_layout:
        output, output_scale = flashinfer_quant_nvfp4_8x4_sf_layout(
            input, input_global_scale
        )
    else:
        # Pre-allocate and call .out variant (same behavior as old in-place API)
        output, output_scale = create_fp4_output_tensors(
            m, n, input.device, is_sf_swizzled_layout
        )
        torch.ops._C.scaled_fp4_quant.out(
            input,
            input_global_scale,
            is_sf_swizzled_layout,
            output=output,
            output_scale=output_scale,
        )

    output_scale = output_scale.view(torch.float8_e4m3fn)
    return output, output_scale