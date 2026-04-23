def sequence_parallelism_pass_on_test_model(
    local_rank: int,
    world_size: int,
    test_model_cls: type[torch.nn.Module],
    custom_ops: str,
    batch_size: int,
    seq_len: int,
    hidden_size: int,
    dtype: torch.dtype,
    fuse_norm_quant: bool,
    dynamic: bool,
):
    set_random_seed(0)

    device = torch.device(f"{DEVICE_TYPE}:{local_rank}")
    torch.accelerator.set_device_index(device)
    torch.set_default_device(device)
    torch.set_default_dtype(dtype)

    update_environment_variables(
        {
            "RANK": str(local_rank),
            "LOCAL_RANK": str(local_rank),
            "WORLD_SIZE": str(world_size),
            "MASTER_ADDR": "localhost",
            "MASTER_PORT": "12345",
        }
    )

    # initialize distributed
    init_distributed_environment()

    # configure vllm config for SequenceParallelismPass
    custom_ops_list = custom_ops.split(",") if custom_ops else []
    compilation_config = CompilationConfig(
        splitting_ops=[],  # avoid automatic rms_norm enablement
        cudagraph_mode=CUDAGraphMode.NONE,  # avoid piecewise warnings
        custom_ops=custom_ops_list,
        pass_config=PassConfig(
            enable_sp=True,
            fuse_norm_quant=fuse_norm_quant,
            eliminate_noops=True,
        ),
    )  # NoOp needed for fusion
    device_config = DeviceConfig(device=torch.device(DEVICE_TYPE))

    # this is a fake model name to construct the model config
    # in the vllm_config, it's not really used.
    model_name = "RedHatAI/Llama-3.2-1B-Instruct-FP8"
    model_config = ModelConfig(
        model=model_name, trust_remote_code=True, dtype=dtype, seed=42
    )

    vllm_config = VllmConfig(
        model_config=model_config,
        device_config=device_config,
        compilation_config=compilation_config,
    )

    with set_current_vllm_config(vllm_config):
        initialize_model_parallel(tensor_model_parallel_size=world_size)
        noop_pass = NoOpEliminationPass(vllm_config)
        sequence_parallelism_pass = SequenceParallelismPass(vllm_config)
        cleanup_pass = PostCleanupPass(vllm_config)
        assert (
            sequence_parallelism_pass.compilation_config.splitting_ops
            == vllm_config.compilation_config.splitting_ops
        )
        assert (
            sequence_parallelism_pass.compilation_config.use_inductor_graph_partition
            == vllm_config.compilation_config.use_inductor_graph_partition
        )
        passes_for_backend: list[VllmInductorPass] = [
            noop_pass,
            sequence_parallelism_pass,
        ]

        if fuse_norm_quant:
            fusion_pass = RMSNormQuantFusionPass(vllm_config)
            passes_for_backend.append(fusion_pass)

        passes_for_backend.append(cleanup_pass)

        backend = TestBackend(*passes_for_backend)

        model = test_model_cls(hidden_size)

        hidden_states = torch.randn((batch_size * seq_len, hidden_size), dtype=dtype)

        if dynamic:
            torch._dynamo.mark_dynamic(hidden_states, 0)

        compiled_model = torch.compile(model, backend=backend)
        compiled_model(hidden_states)

        assert sequence_parallelism_pass.matched_count == 4

        # In pre-nodes, all reduce should be there,
        # reduce scatter and all gather should not
        for op in model.ops_in_model_before():
            assert backend.op_count(op, before=True) == 4

        # In post-nodes, reduce scatter and all gather should be there,
        # all reduce should not
        for op in model.ops_in_model_after():
            assert backend.op_count(op, before=False) == 4

        for op in model.ops_in_model():
            assert backend.op_count(op, before=False) > 0