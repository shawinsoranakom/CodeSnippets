def _test_cp_gsm8k(
    model_id: str,
    parallel_setup: ParallelSetup,
    distributed_backend: str,
    runner: RunnerOption,
    test_options: CPTestOptions,
    num_gpus_available: int,
    *,
    method: Literal["generate"],
    is_multimodal: bool,
):
    (
        tp_size,
        pp_size,
        dcp_size,
        cp_kv_cache_interleave_size,
        eager_mode,
        chunked_prefill,
    ) = parallel_setup

    multi_node_only, attn_backend = test_options

    model_info = HF_EXAMPLE_MODELS.find_hf_info(model_id)
    model_info.check_transformers_version(on_fail="skip")

    trust_remote_code = model_info.trust_remote_code
    tokenizer_mode = model_info.tokenizer_mode
    hf_overrides = model_info.hf_overrides

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

    server_args = [
        # use half precision for speed and memory savings in CI environment
        "--dtype",
        "bfloat16",
        "--max-model-len",
        "4096",
        "--max-num-seqs",
        "64",
    ]
    if chunked_prefill:
        server_args.append("--enable-chunked-prefill")
    if eager_mode:
        server_args.append("--enforce-eager")
    if runner != "auto":
        server_args.extend(["--runner", runner])
    if trust_remote_code:
        server_args.append("--trust-remote-code")
    if tokenizer_mode:
        server_args.extend(["--tokenizer-mode", tokenizer_mode])
    if hf_overrides:
        server_args.extend(["--hf-overrides", json.dumps(hf_overrides)])

    server_args.extend(
        [
            "--tensor-parallel-size",
            str(tp_size),
            "--pipeline-parallel-size",
            str(pp_size),
            "--decode-context-parallel-size",
            str(dcp_size),
            "--dcp-kv-cache-interleave-size",
            str(cp_kv_cache_interleave_size),
            "--distributed-executor-backend",
            distributed_backend,
        ]
    )

    if attn_backend:
        server_args.append(f"--attention-backend={attn_backend}")

    with RemoteOpenAIServer(
        model_id,
        server_args,
        max_wait_seconds=720,
    ) as remote_server:
        host = f"http://{remote_server.host}"
        port = remote_server.port

        # Run GSM8K evaluation
        results = evaluate_gsm8k(
            num_questions=NUM_QUESTIONS,
            num_shots=NUM_SHOTS,
            host=host,
            port=port,
        )

        # Validate accuracy is reasonable
        accuracy = results["accuracy"]
        min_accuracy = MIN_ACCURACY[model_id]
        assert accuracy >= min_accuracy, (
            f"TP+DCP accuracy too low: {accuracy:.3f} < {min_accuracy:.3f}"
        )