def run_single_backend_sdpa(
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
    backend_context = get_backend_context(backend)
    with backend_context:
        _device = torch.device("cuda")

        eager_sdpa = generate_eager_sdpa(
            config.attn_type, config.shape, config.dtype, block_mask, score_mod
        )

        if config.attn_type == "document_mask":
            q_eager, k_eager, v_eager = generate_jagged_inputs(
                config.shape, query, key, value, **mask_kwargs
            )
            q_eager = q_eager.transpose(1, 2).requires_grad_(query.requires_grad)
            k_eager = k_eager.transpose(1, 2).requires_grad_(key.requires_grad)
            v_eager = v_eager.transpose(1, 2).requires_grad_(value.requires_grad)
        else:
            q_eager, k_eager, v_eager = query_key_value_clones(query, key, value)

        if eager_sdpa:
            try:
                out_eager = eager_sdpa(query=q_eager, key=k_eager, value=v_eager)
            except RuntimeError as e:
                print(
                    f"[SKIP] SDPA Backend {backend} for shape {config.shape}. \n\t\t\tError encountered: {e} "
                )
                return ExperimentResults(
                    fwd_time=float("nan"),
                    bwd_time=float("nan") if config.calculate_bwd_time else None,
                )
            if config.attn_type in ["document_mask"]:
                flatten_o_eager = torch.cat(torch.unbind(out_eager.transpose(1, 2)))
                flatten_o_compile = out_compile.transpose(1, 2).flatten(
                    start_dim=0, end_dim=1
                )
                torch.testing.assert_close(
                    flatten_o_eager, flatten_o_compile, atol=1e-2, rtol=1e-2
                )
            elif not (
                config.attn_type in ["rel", "alibi"]
                and config.dtype in [torch.float16, torch.bfloat16]
            ):  # rel has accuracy issue with 16bit floats
                torch.testing.assert_close(out_eager, out_compile, atol=1e-2, rtol=1e-2)

        if eager_sdpa:
            forward_eager_time = benchmark_torch_function_in_microseconds(
                eager_sdpa, query=q_eager, key=k_eager, value=v_eager
            )
        else:
            forward_eager_time = float("nan")

        if config.calculate_bwd_time:
            # TODO: debug backward pass for njt
            if eager_sdpa and config.attn_type != "document_mask":
                d_out = torch.randn_like(out_eager.transpose(1, 2)).transpose(1, 2)
                backward_eager_time = benchmark_torch_function_in_microseconds(
                    out_eager.backward, d_out, retain_graph=True
                )
            else:
                backward_eager_time = float("nan")

            return ExperimentResults(
                fwd_time=forward_eager_time,
                bwd_time=backward_eager_time,
            )
        else:
            return ExperimentResults(
                fwd_time=forward_eager_time,
                bwd_time=None,
            )