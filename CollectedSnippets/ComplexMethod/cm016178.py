def run_single_experiment(
    config: ExperimentConfig,
    dynamic=False,
) -> dict[str, ExperimentResults]:
    device = torch.device("cuda")
    batch_size, q_heads, q_seq_len, kv_heads, kv_seq_len, head_dim = config.shape
    query, key, value = generate_inputs(
        batch_size,
        q_heads,
        q_seq_len,
        kv_heads,
        kv_seq_len,
        head_dim,
        config.dtype,
        device,
        requires_grad=config.calculate_bwd_time,
        nested_tensors=config.attn_type == "document_mask",
    )
    score_mod = generate_score_mod(config.attn_type, config.shape)
    block_mask, mask_kwargs = generate_block_mask(config.attn_type, config.shape)
    kernel_options = get_kernel_options(config.attn_type, config.shape)

    if config.max_autotune:
        compiled_sdpa = torch.compile(
            flex_attention, dynamic=dynamic, mode="max-autotune-no-cudagraphs"
        )
    else:
        compiled_sdpa = torch.compile(flex_attention, dynamic=dynamic)

    out_compile = compiled_sdpa(
        query=query,
        key=key,
        value=value,
        score_mod=score_mod,
        block_mask=block_mask,
        enable_gqa=True,
        kernel_options=kernel_options,
    )

    forward_compiled_time = benchmark_torch_function_in_microseconds(
        compiled_sdpa,
        query,
        key,
        value,
        score_mod=score_mod,
        block_mask=block_mask,
        enable_gqa=True,
        kernel_options=kernel_options,
    )

    results = {}
    for backend in config.backends:
        if backend in ["fav3", "fakv"]:
            results[backend] = run_single_backend_FA(
                config,
                query,
                key,
                value,
                out_compile,
                score_mod,
                block_mask,
                mask_kwargs,
                backend,
            )
        else:  # sdpa (also supports fav2)
            results[backend] = run_single_backend_sdpa(
                config,
                query,
                key,
                value,
                out_compile,
                score_mod,
                block_mask,
                mask_kwargs,
                backend,
            )

    if config.calculate_bwd_time:
        d_out = torch.randn_like(out_compile)
        backward_compile_time = benchmark_torch_function_in_microseconds(
            out_compile.backward, d_out, retain_graph=True
        )
    sparsity = block_mask.sparsity() / 100.0 if block_mask is not None else 0.0
    sparsity = sparsity if config.attn_type != "document_mask" else 0.5

    results["flex"] = ExperimentResults(
        fwd_time=forward_compiled_time,
        bwd_time=backward_compile_time if config.calculate_bwd_time else None,
        sparsity=sparsity,
    )

    return results