def test_moe_layer(
    dp_size: int,
    tp_size: int,
    use_ep: bool,
    backend: str,
    enable_eplb: bool,
    monkeypatch,
    pytestconfig,
    subtests,
):
    """Test MoE layer with parallelism (multi-GPU or TP/EP enabled).

    For non-parallel cases (world_size == 1), use test_moe_layer_no_parallel instead.
    """
    num_gpus = current_platform.device_count()
    world_size = tp_size * dp_size
    ep_size = 1 if not use_ep else world_size  # or dp_size?
    assert world_size > 1

    # Check if enough GPUs available
    if world_size is not None and num_gpus is not None and world_size > num_gpus:
        pytest.skip(f"Not enough GPUs got {num_gpus}, expected {world_size}.")

    if enable_eplb and not use_ep:
        pytest.skip("EPLB requires EP.")

    verbosity = pytestconfig.getoption("verbose")

    if os.environ.get("VLLM_LOGGING_LEVEL") is None:
        monkeypatch.setenv("VLLM_LOGGING_LEVEL", "ERROR")

    # TODO
    # VLLM_FLASHINFER_MOE_BACKEND=latency
    # VLLM_USE_FLASHINFER_MOE_FP16=1
    # VLLM_USE_FLASHINFER_MOE_FP8
    # VLLM_USE_FLASHINFER_MOE_FP4
    # VLLM_USE_FLASHINFER_MOE_INT4

    parallel_config = ParallelConfig(
        pipeline_parallel_size=1,
        data_parallel_size=dp_size,
        tensor_parallel_size=tp_size,
        enable_expert_parallel=use_ep,
        all2all_backend=backend,
        enable_eplb=enable_eplb,
    )

    compilation_config = CompilationConfig()
    # compilation_config.mode = CompilationMode.NONE  # for now
    compilation_config.pass_config.fuse_allreduce_rms = False  # for now

    vllm_config = VllmConfig(
        parallel_config=parallel_config,
        compilation_config=compilation_config,
        scheduler_config=SchedulerConfig.default_factory(
            max_num_batched_tokens=next_power_of_2(MAX_M)
        ),
    )

    test_configs = generate_valid_test_configs(
        backend, ep_size, dp_size, tp_size, enable_eplb, verbosity
    )

    if subtests is not None:
        new_test_configs = []
        for subtest in subtests.split(","):
            sub_test_config = MoETestConfig.from_id(subtest)
            if sub_test_config in test_configs:
                new_test_configs.append(sub_test_config)
            else:
                pytest.skip(
                    f"subtest config {subtest} does not match any valid test "
                    "configuration"
                )
        test_configs = new_test_configs

    if len(test_configs) == 0:
        pytest.skip("No supported configs found for this testpoint.")

    try:
        parallel_launch_with_config(
            world_size,
            _parallel_worker,
            vllm_config,
            None,
            test_configs,
            verbosity,
        )
    finally:
        torch.accelerator.synchronize()  # TODO: Is this needed?
        torch.accelerator.empty_cache()