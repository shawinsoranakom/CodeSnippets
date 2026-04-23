def _compare_sp(
    model_id: str,
    parallel_setup: ParallelSetup,
    distributed_backend: str,
    runner: RunnerOption,
    test_options: SPTestOptions,
    num_gpus_available: int,
    use_inductor_graph_partition: bool,
    fuse_gemm_comms: bool,
    *,
    method: Literal["generate", "encode"],
    is_multimodal: bool,
):
    (
        tp_size,
        pp_size,
        fuse_norm_quant,
        fuse_act_quant,
        eager_mode,
        chunked_prefill,
    ) = parallel_setup

    multi_node_only, load_format = test_options

    model_info = HF_EXAMPLE_MODELS.find_hf_info(model_id)
    model_info.check_transformers_version(on_fail="skip")

    trust_remote_code = model_info.trust_remote_code
    tokenizer_mode = model_info.tokenizer_mode
    hf_overrides = model_info.hf_overrides
    require_embed_inputs = model_info.require_embed_inputs

    if load_format == "dummy":
        # Avoid OOM
        text_overrides = {
            "num_hidden_layers": 4,
            "hidden_size": 512,
            "intermediate_size": 800,
            "num_attention_heads": 4,
            "num_key_value_heads": 1,
        }

        if is_multimodal:
            hf_overrides.update({"text_config": text_overrides})
        else:
            hf_overrides.update(text_overrides)
    else:
        model_info.check_available_online(on_fail="skip")

    if num_gpus_available < tp_size * pp_size:
        pytest.skip(f"Need at least {tp_size} x {pp_size} GPUs")
    if VLLM_MULTI_NODE and distributed_backend == "mp":
        pytest.skip(
            "Skipping multi-node pipeline parallel test for "
            "multiprocessing distributed backend"
        )
    if multi_node_only and not VLLM_MULTI_NODE:
        pytest.skip("Not in multi-node setting")

    common_args = [
        # use half precision for speed and memory savings in CI environment
        "--dtype",
        "float16",
        "--max-model-len",
        "2048",
        "--max-num-seqs",
        "8",
    ]
    if chunked_prefill:
        common_args.append("--enable-chunked-prefill")
    if eager_mode:
        common_args.append("-cc.cudagraph_mode=none")
    if runner != "auto":
        common_args.extend(["--runner", runner])
    if trust_remote_code:
        common_args.append("--trust-remote-code")
    if tokenizer_mode:
        common_args.extend(["--tokenizer-mode", tokenizer_mode])
    if load_format:
        common_args.extend(["--load-format", load_format])
    if hf_overrides:
        common_args.extend(["--hf-overrides", json.dumps(hf_overrides)])
    if require_embed_inputs:
        common_args.extend(
            [
                "--skip-tokenizer-init",
                "--enable-prompt-embeds",
                "--enable-mm-embeds",
            ]
        )

    compilation_config = {
        "mode": CompilationMode.VLLM_COMPILE,
        "compile_sizes": [4, 8],
        "pass_config": {
            "enable_sp": True,
            "fuse_gemm_comms": fuse_gemm_comms,
            "fuse_norm_quant": fuse_norm_quant,
            "fuse_act_quant": fuse_act_quant,
            "eliminate_noops": True,
        },
        "use_inductor_graph_partition": use_inductor_graph_partition,
    }

    tp_sp_args = [
        *common_args,
        "--tensor-parallel-size",
        str(tp_size),
        "--pipeline-parallel-size",
        str(pp_size),
        "--distributed-executor-backend",
        distributed_backend,
        "--compilation_config",
        json.dumps(compilation_config),
    ]

    tp_args = [
        *common_args,
        "--tensor-parallel-size",
        str(tp_size),
        "--distributed-executor-backend",
        "mp",
    ]

    compare_two_settings(model_id, tp_sp_args, tp_args, method=method)