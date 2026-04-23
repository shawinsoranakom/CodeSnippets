def rank_worker(
    pgi: ProcessGroupInfo,
    vllm_config: VllmConfig,
    cpu_group,
    base_config: Config,
    weights: WeightTensors,
    verbose: bool,
):
    # Initialize workspace manager in child process
    device = torch.device(f"cuda:{pgi.local_rank}")
    init_workspace_manager(device)

    set_random_seed(pgi.rank)

    # get weights to this device
    weights.to_current_device()

    Ms = base_config.Ms
    assert isinstance(Ms, list)
    TOPKs = base_config.topks
    assert isinstance(TOPKs, list)

    exceptions = []
    count = 0

    for m, topk in product(Ms, TOPKs):
        # override m and topk
        config = copy.deepcopy(base_config)
        config.Ms = m
        config.topks = topk

        try:
            print(f"Running[{pgi.rank}]: m={m}, topk={topk} ...")
            count = count + 1

            # inputs for rank
            rank_tensors = RankTensors.make(config, pgi)

            # Skip unsupported: AITER block-scaled MoE does not
            # support apply_router_weight_on_input (topk=1 path).
            # https://github.com/ROCm/aiter/issues/2418
            if (
                topk == 1
                and config.supports_apply_weight_on_input()
                and getattr(config.fused_experts_type, "__name__", "") == "AiterExperts"
                and config.quant_block_shape is not None
            ):
                print(
                    f"Skipping[{pgi.rank}]: m={m}, topk={topk}"
                    " (AITER block-scaled + weight-on-input,"
                    " https://github.com/ROCm/aiter/issues/2418)"
                )
                count -= 1
                continue

            # modular kernel out
            mk_out = run_modular_kernel(pgi, vllm_config, config, weights, rank_tensors)

            with set_current_vllm_config(vllm_config):
                ref_out = reference_moe_impl(config, weights, rank_tensors)

            if config.quant_dtype == "nvfp4":
                atol = 1e-1 if config.K < 4096 else 2e-1
                rtol = 1e-1 if config.K < 4096 else 2e-1
            else:
                atol = 3e-2
                rtol = 3e-2

            # On ROCm, AITER FP8 fused MoE uses hardware FP8
            # dot-product which can produce slightly larger error
            # than dequant+f32 matmul at FP8 representable-value
            # boundaries. Allow a small percentage of elements to
            # exceed the base tolerance by a bounded margin.
            # https://github.com/ROCm/aiter/issues/2421
            from vllm.platforms import current_platform as _cp

            is_aiter_fp8 = (
                _cp.is_rocm()
                and getattr(config.fused_experts_type, "__name__", "") == "AiterExperts"
                and config.quant_config is not None
            )
            if is_aiter_fp8:
                diff = (ref_out - mk_out).abs()
                n_total = diff.numel()
                max_diff = diff.max().item()
                n_exceed = int((diff > atol).sum().item())
                pct_exceed = n_exceed / n_total * 100
                # FP8 hw matmul vs f32 reference: up to ~4% of
                # elements may exceed base tolerance, but max
                # error should stay within 3x base tolerance.
                max_pct_allowed = 5.0
                relaxed_atol = atol * 4
                print(
                    f"[AITER FP8 precision] "
                    f"max_diff={max_diff:.6f}, "
                    f"exceed_atol={n_exceed}/{n_total} "
                    f"({pct_exceed:.4f}%), "
                    f"max_pct_allowed={max_pct_allowed}%, "
                    f"relaxed_limit={relaxed_atol}"
                )
                assert pct_exceed <= max_pct_allowed, (
                    f"AITER FP8: {pct_exceed:.2f}% elements exceed "
                    f"atol={atol} (max allowed {max_pct_allowed}%)"
                )
                assert max_diff <= relaxed_atol, (
                    f"AITER FP8: max_diff={max_diff:.6f} exceeds "
                    f"relaxed limit {relaxed_atol}"
                )
            else:
                torch.testing.assert_close(ref_out, mk_out, atol=atol, rtol=rtol)
            format_result(verbose, config.describe())
        except Exception as ex:
            format_result(verbose, config.describe(), ex)
            exceptions.append(ex)

    if len(exceptions) > 0:
        raise RuntimeError(
            f"{len(exceptions)} of {count} tests failed in child process, "
            f"rank={pgi.rank}."
        )
    else:
        print(f"{count} of {count} tests passed in child process, rank={pgi.rank}.")