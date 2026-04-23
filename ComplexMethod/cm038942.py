def benchmark_config(
    config: BenchmarkConfig,
    num_tokens: int,
    num_experts: int,
    shard_intermediate_size: int,
    hidden_size: int,
    topk: int,
    dtype: torch.dtype,
    use_fp8_w8a8: bool,
    use_int8_w8a16: bool,
    use_int4_w4a16: bool = False,
    num_iters: int = 100,
    block_quant_shape: list[int] = None,
    use_deep_gemm: bool = False,
) -> float:
    init_dtype = torch.float16 if use_fp8_w8a8 else dtype
    x = torch.randn(num_tokens, hidden_size, dtype=dtype)
    if use_int4_w4a16:
        # Int4 packed weights: 2 int4 values per uint8 byte
        # K dimension is packed (halved)
        intermediate_size = shard_intermediate_size // 2  # after silu_and_mul
        w1 = torch.randint(
            0,
            255,
            (
                num_experts,
                shard_intermediate_size,
                hidden_size // 2,  # int4 packing
            ),
            dtype=torch.uint8,
        )
        w2 = torch.randint(
            0,
            255,
            (
                num_experts,
                hidden_size,
                intermediate_size // 2,  # int4 packing
            ),
            dtype=torch.uint8,
        )
    elif use_int8_w8a16:
        w1 = torch.randint(
            -127,
            127,
            (
                num_experts,
                shard_intermediate_size,
                hidden_size,
            ),
            dtype=torch.int8,
        )
        w2 = torch.randint(
            -127,
            127,
            (
                num_experts,
                hidden_size,
                shard_intermediate_size // 2,
            ),
            dtype=torch.int8,
        )
    else:
        w1 = torch.randn(
            num_experts, shard_intermediate_size, hidden_size, dtype=init_dtype
        )
        w2 = torch.randn(
            num_experts, hidden_size, shard_intermediate_size // 2, dtype=init_dtype
        )
    gating_output = torch.randn(num_iters, num_tokens, num_experts, dtype=torch.float32)

    w1_scale = None
    w2_scale = None
    a1_scale = None
    a2_scale = None
    if use_int4_w4a16:
        if block_quant_shape is None:
            raise ValueError("block_quant_shape is required for int4_w4a16")
        group_size = block_quant_shape[1]
        # Scales shape: (E, N, K // group_size) in fp16
        w1_scale = torch.rand(
            (num_experts, shard_intermediate_size, hidden_size // group_size),
            dtype=dtype,
        )
        w2_scale = torch.rand(
            (num_experts, hidden_size, intermediate_size // group_size),
            dtype=dtype,
        )
    elif use_int8_w8a16:
        w1_scale = torch.randn(
            (num_experts, 2 * shard_intermediate_size), dtype=torch.float32
        )
        w2_scale = torch.randn((hidden_size, num_experts), dtype=torch.float32)
    if use_deep_gemm:
        # we use the default block shape for deepgemm
        block_quant_shape = [128, 128]
    if use_fp8_w8a8:
        if block_quant_shape:
            block_n, block_k = block_quant_shape[0], block_quant_shape[1]
            E = num_experts
            N = shard_intermediate_size // 2
            K = hidden_size
            factor_for_scale = 1e-2
            n_tiles_w1 = (2 * N + block_n - 1) // block_n
            n_tiles_w2 = (K + block_n - 1) // block_n
            k_tiles_w1 = (K + block_k - 1) // block_k
            k_tiles_w2 = (N + block_k - 1) // block_k
            w1_scale = (
                torch.rand((E, n_tiles_w1, k_tiles_w1), dtype=torch.float32)
                * factor_for_scale
            )
            w2_scale = (
                torch.rand((E, n_tiles_w2, k_tiles_w2), dtype=torch.float32)
                * factor_for_scale
            )
        else:
            w1_scale = torch.randn(num_experts, dtype=torch.float32)
            w2_scale = torch.randn(num_experts, dtype=torch.float32)

        a1_scale = torch.randn(1, dtype=torch.float32)
        a2_scale = torch.randn(1, dtype=torch.float32)

        w1 = w1.to(FP8_DTYPE)
        w2 = w2.to(FP8_DTYPE)

    input_gating = torch.empty(num_tokens, num_experts, dtype=torch.float32)

    def prepare(i: int):
        input_gating.copy_(gating_output[i])

    def run():
        from vllm.model_executor.layers.fused_moe import override_config

        if use_fp8_w8a8:
            quant_dtype = torch.float8_e4m3fn
        elif use_int8_w8a16:
            quant_dtype = torch.int8
        else:
            quant_dtype = None

        quant_config = FusedMoEQuantConfig.make(
            quant_dtype=quant_dtype,
            w1_scale=w1_scale,
            w2_scale=w2_scale,
            a1_scale=a1_scale,
            a2_scale=a2_scale,
            block_shape=block_quant_shape,
            weight_dtype="int4" if use_int4_w4a16 else None,
        )

        deep_gemm_experts = None
        if use_deep_gemm:
            moe_config = (
                FusedMoEConfig(
                    num_experts=num_experts,
                    experts_per_token=topk,
                    hidden_dim=hidden_size,
                    intermediate_size_per_partition=shard_intermediate_size,
                    num_local_experts=num_experts,
                    num_logical_experts=num_experts,
                    activation=MoEActivation.SILU,
                    moe_parallel_config=FusedMoEParallelConfig.make_no_parallel(),
                    in_dtype=init_dtype,
                    routing_method=RoutingMethodType.TopK,
                    device="cuda",
                ),
            )
            deep_gemm_experts = mk.FusedMoEKernel(
                prepare_finalize=maybe_make_prepare_finalize(
                    moe=moe_config,
                    quant_config=quant_config,
                    allow_new_interface=True,
                    use_monolithic=False,
                ),
                fused_experts=TritonOrDeepGemmExperts(
                    moe_config=moe_config,
                    quant_config=quant_config,
                ),
                inplace=not disable_inplace(),
            )

        with override_config(config):
            topk_weights, topk_ids, token_expert_indices = fused_topk(
                x, input_gating, topk, renormalize=not use_deep_gemm
            )

            inplace = not disable_inplace()
            if use_deep_gemm:
                return deep_gemm_experts.apply(
                    x,
                    w1,
                    w2,
                    topk_weights,
                    topk_ids,
                    activation=MoEActivation.SILU,
                    global_num_experts=num_experts,
                    apply_router_weight_on_input=False,
                    expert_map=False,
                )
            return fused_experts(
                x,
                w1,
                w2,
                topk_weights,
                topk_ids,
                inplace=inplace,
                quant_config=quant_config,
            )

    # JIT compilation & warmup
    run()
    torch.accelerator.synchronize()

    # Capture 10 invocations with CUDA graph
    graph = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph):
        for _ in range(10):
            run()
    torch.accelerator.synchronize()

    # Warmup
    for _ in range(5):
        graph.replay()
    torch.accelerator.synchronize()

    start_event = torch.Event(enable_timing=True)
    end_event = torch.Event(enable_timing=True)

    latencies: list[float] = []
    for i in range(num_iters):
        prepare(i)
        torch.accelerator.synchronize()

        start_event.record()
        graph.replay()
        end_event.record()
        end_event.synchronize()
        latencies.append(start_event.elapsed_time(end_event))
    avg = sum(latencies) / (num_iters * 10) * 1000  # us
    graph.reset()
    return avg