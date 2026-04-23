def run_single_experiment(config: ExperimentConfig) -> ExperimentResults:
    q, k, v = get_input(config)
    is_causal = config.is_causal
    context = (
        sdpa_kernel(config.backend) if config.backend is not None else nullcontext()
    )

    # Activate flash attention implementation if specified
    if config.backend is SDPBackend.FLASH_ATTENTION and config.flash_impl in (
        "FA3",
        "FA4",
    ):
        try:
            activate_flash_attention_impl(config.flash_impl)
        except ImportError as e:
            raise RuntimeError(
                f"Failed to activate {config.flash_impl}: {e}\n"
                f"Please install the required flash attention library or run with default configuration (without --flash_test)."
            ) from e

    try:
        with context:
            forward_time = benchmark_cuda_function_in_microseconds(
                scaled_dot_product_attention,
                q,
                k,
                v,
                is_causal=is_causal,
                attn_mask=None,
            )
            out_torch = scaled_dot_product_attention(
                q, k, v, is_causal=is_causal, attn_mask=None
            )
            d_out = torch.randn_like(out_torch)
            backward_time = benchmark_cuda_function_in_microseconds(
                out_torch.backward, d_out, retain_graph=True
            )
    finally:
        # Restore default FA2 implementation if we activated a different one
        if config.backend is SDPBackend.FLASH_ATTENTION and config.flash_impl in (
            "FA3",
            "FA4",
        ):
            restore_flash_attention_impl()

    # Calculate TFLOPS for forward and backward passes
    sparsity = 0.5 if is_causal else 0.0
    forward_tflops = calculate_tflops(config, forward_time, sparsity=sparsity)
    backward_tflops = calculate_tflops(
        config, backward_time, is_backward=True, sparsity=sparsity
    )

    return ExperimentResults(
        forward_time=forward_time,
        backward_time=backward_time,
        forward_tflops=forward_tflops,
        backward_tflops=backward_tflops,
    )