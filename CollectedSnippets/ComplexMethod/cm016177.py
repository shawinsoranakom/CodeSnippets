def run_single_backend_FA(
    config: ExperimentConfig,
    query: torch.Tensor,
    key: torch.Tensor,
    value: torch.Tensor,
    out_compile: torch.Tensor,
    score_mod: Callable | None,
    block_mask: BlockMask | None,
    mask_kwargs,
    backend: str,
) -> ExperimentResults:
    if backend not in ["fav3", "fakv"]:
        raise AssertionError(f"backend must be 'fav3' or 'fakv', got {backend}")
    # Generate callable for specific backend.
    if backend in ["fav3"]:
        FA = generate_FA_callable(
            config.attn_type, config.shape, config.dtype, backend, **mask_kwargs
        )
    elif backend == "fakv":
        FA = generate_FD_callable(config.attn_type, config.shape, config.dtype)

    q_FA, k_FA, v_FA = query_key_value_clones(query, key, value)
    q_FA, k_FA, v_FA = q_FA.transpose(1, 2), k_FA.transpose(1, 2), v_FA.transpose(1, 2)
    if config.attn_type == "document_mask":
        q_FA = q_FA.flatten(start_dim=0, end_dim=1)
        k_FA = k_FA.flatten(start_dim=0, end_dim=1)
        v_FA = v_FA.flatten(start_dim=0, end_dim=1)

    if FA:
        out_FA = FA(q=q_FA, k=k_FA, v=v_FA)
        if config.attn_type in ["document_mask"]:
            out_FA_updated = out_FA[None, :, :, :]
        else:
            out_FA_updated = out_FA

        if not (
            config.attn_type in ["rel", "alibi"]
            and config.dtype in [torch.float16, torch.bfloat16]
        ):
            torch.testing.assert_close(
                out_FA_updated, out_compile.transpose(1, 2), atol=1e-2, rtol=1e-2
            )

    if FA:
        forward_FA_time = benchmark_torch_function_in_microseconds(
            FA, q=q_FA, k=k_FA, v=v_FA
        )
    else:
        forward_FA_time = float("nan")

    if config.calculate_bwd_time:
        if FA:
            d_out = torch.randn_like(out_FA)
            backward_FA_time = benchmark_torch_function_in_microseconds(
                out_FA.backward, d_out, retain_graph=True
            )
        else:
            backward_FA_time = float("nan")

    return ExperimentResults(
        fwd_time=forward_FA_time,
        bwd_time=backward_FA_time if config.calculate_bwd_time else None,
    )