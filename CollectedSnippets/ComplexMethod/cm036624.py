def _compare_tp(
    model_id: str,
    parallel_setup: ParallelSetup,
    distributed_backend: str,
    runner: RunnerOption,
    test_options: PPTestOptions,
    num_gpus_available: int,
    *,
    method: Literal["generate", "encode"],
    is_multimodal: bool,
):
    (
        tp_size,
        pp_size,
        eager_mode,
    ) = parallel_setup

    multi_node_only, load_format = test_options

    model_info = HF_EXAMPLE_MODELS.find_hf_info(model_id)
    model_info.check_transformers_version(on_fail="skip")

    trust_remote_code = model_info.trust_remote_code
    tokenizer_mode = model_info.tokenizer_mode
    hf_overrides = model_info.hf_overrides
    hf_config = get_config(model_id, trust_remote_code)
    require_embed_inputs = model_info.require_embed_inputs
    max_num_seqs = model_info.max_num_seqs
    enable_prefix_caching = model_info.enable_prefix_caching

    dtype = "float16"
    if hf_config.model_type in _FLOAT16_NOT_SUPPORTED_MODELS:
        dtype = "bfloat16"

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
        dtype,
        "--max-model-len",
        "2048",
        "--max-num-seqs",
        "8",
    ]
    if eager_mode:
        common_args.append("--enforce-eager")
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
    if not enable_prefix_caching:
        common_args.append("--no-enable-prefix-caching")
    if require_embed_inputs:
        common_args.extend(
            [
                "--skip-tokenizer-init",
                "--enable-prompt-embeds",
                "--enable-mm-embeds",
            ]
        )
    if max_num_seqs:
        common_args.extend(["--max-num-seqs", f"{max_num_seqs}"])

    if distributed_backend == "ray":
        # Test Ray Compiled Graph for all the tests
        pp_env = {
            "VLLM_USE_RAY_COMPILED_DAG_NCCL_CHANNEL": "1",
        }
    elif distributed_backend == "mp":
        pp_env = None
    else:
        pp_env = None

    tp_env = None

    pp_args = [
        *common_args,
        "--pipeline-parallel-size",
        str(pp_size),
        "--tensor-parallel-size",
        str(tp_size),
        "--distributed-executor-backend",
        distributed_backend,
    ]

    # compare without pipeline parallelism
    # NOTE: use mp backend for TP
    # PP tests might involve multiple nodes, and ray might
    #  schedule all workers in a node other than the head node,
    #  which can cause the test to fail.
    tp_args = [
        *common_args,
        "--tensor-parallel-size",
        str(tp_size),
        "--distributed-executor-backend",
        "mp",
    ]

    compare_two_settings(model_id, pp_args, tp_args, pp_env, tp_env, method=method)