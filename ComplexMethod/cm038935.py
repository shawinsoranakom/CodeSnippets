def bench_optype(
    ctx: BenchmarkContext,
    arg_pool_size: int,
    op_type: OpType,
    cuda_graph_nops: int | None = None,
    expand_fn_add_inputs: bool | None = None,
    test_correctness: bool = False,
) -> TMeasurement:
    assert arg_pool_size >= 1
    if op_type.is_shrink_fn() or op_type.is_fused_moe_lora_fn():
        assert expand_fn_add_inputs is None
    else:
        assert expand_fn_add_inputs is not None

    # BenchmarkContext -> BenchmarkTensors
    bench_tensors: list[BenchmarkTensors] = [
        BenchmarkTensors.make(ctx, op_type) for _ in range(arg_pool_size)
    ]
    for bt in bench_tensors:
        bt.sanity_check(ctx, op_type)

    # Test correctness of our implementation.
    if test_correctness:
        assert op_type in [OpType.LORA_SHRINK, OpType.LORA_EXPAND], (
            f"Correctness testing is not supported for {op_type.name}."
        )
        assert all(
            [
                bt.test_correctness(ctx, op_type, expand_fn_add_inputs)
                for bt in bench_tensors
            ]
        )

    # BenchmarkTensors -> dict (kwargs)
    kwargs_list = [
        bt.bench_fn_kwargs(ctx, op_type, add_inputs=expand_fn_add_inputs)
        for bt in bench_tensors
    ]

    # Clear LoRA optimization hash-maps.
    _LORA_A_PTR_DICT.clear()
    _LORA_B_PTR_DICT.clear()
    _LORA_PTR_DICT.clear()
    # Run bench function so that _LORA_A_PTR_DICT and _LORA_B_PTR_DICT are set up
    for kwargs in kwargs_list:
        op_type.bench_fn()(**kwargs)
    torch.accelerator.synchronize()

    # Merge into a single kwargs and qualify arguments as ArgPool
    kwargs = {k: ArgPool([]) for k in kwargs_list[0]}
    for _kwargs in kwargs_list:
        for k, v in _kwargs.items():
            kwargs[k].values.append(v)

    describe_args = (
        f"add_inputs={expand_fn_add_inputs}" if expand_fn_add_inputs is not None else ""
    )
    description = f"{op_type.name}({describe_args}) ({bench_tensors[0].io_types()})"

    cuda_graph_params = None
    if cuda_graph_nops:
        cuda_graph_params = CudaGraphBenchParams(cuda_graph_nops)
    timer = None
    with Bench(
        cuda_graph_params,
        ctx.bench_label(),
        ctx.bench_sublabel(op_type),
        description,
        op_type.bench_fn(),
        **kwargs,
    ) as bench:
        timer = bench.run()
    return timer