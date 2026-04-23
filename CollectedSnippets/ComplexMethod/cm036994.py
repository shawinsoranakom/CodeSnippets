def llm_pair(request):
    model, backend_config, use_inductor_graph_partition = request.param
    backend_config.comp_config["use_inductor_graph_partition"] = (
        use_inductor_graph_partition
    )

    if use_inductor_graph_partition and not is_torch_equal_or_newer("2.9.0.dev"):
        pytest.skip("Inductor graph partition only supported in torch>=2.9")

    # Dynamically skip test if GPU capability is not met
    if (
        backend_config.specific_gpu_arch
        and backend_config.specific_gpu_arch != current_platform.get_device_capability()
    ):
        if backend_config.specific_gpu_arch == (9, 0):
            pytest.skip("Only Hopper GPUs support FA3 and FlashMLA")
        elif backend_config.specific_gpu_arch == (10, 0):
            pytest.skip("Only Blackwell GPUs support Cutlass MLA")

    # FlashInfer is not supported on ROCm
    if backend_config == AttentionBackendEnum.FLASHINFER and current_platform.is_rocm():
        pytest.skip("FlashInfer is not supported on ROCm")

    env_vars = {
        # Force native sampler to avoid potential nondeterminism in FlashInfer
        # when per-request generators are not used in V1.
        "VLLM_USE_FLASHINFER_SAMPLER": "0",
    }
    with temporary_environ(env_vars):
        full = LLM(
            model=model,
            gpu_memory_utilization=0.43,
            trust_remote_code=True,
            max_model_len=1024,
            max_num_seqs=128,
            compilation_config=CompilationConfig(**backend_config.comp_config),
            generation_config="vllm",
            seed=42,
        )
        piecewise = LLM(
            model=model,
            gpu_memory_utilization=0.43,
            trust_remote_code=True,
            max_model_len=1024,
            max_num_seqs=128,
            compilation_config=CompilationConfig(cudagraph_mode="PIECEWISE"),
            generation_config="vllm",
            seed=42,
        )

    # PyTest caches the fixture values so we use weakref.proxy to enable GC
    yield weakref.proxy(full), weakref.proxy(piecewise)
    del full
    del piecewise

    wait_for_gpu_memory_to_clear(
        devices=[0],
        threshold_ratio=0.1,
    )