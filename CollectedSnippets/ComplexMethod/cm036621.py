def _compare_tp(
    model_name: str,
    parallel_setup: ParallelSetup,
    distributed_backend: str,
    runner: RunnerOption,
    test_options: EPTestOptions,
    num_gpus_available: int,
    *,
    method: Literal["generate"],
):
    (
        tp_size,
        eager_mode,
        chunked_prefill,
    ) = parallel_setup
    (
        trust_remote_code,
        tokenizer_mode,
        load_format,
        hf_overrides,
    ) = test_options

    if num_gpus_available < tp_size:
        pytest.skip(f"Need at least {tp_size} GPUs")

    common_args = [
        # use half precision for speed and memory savings in CI environment
        "--dtype",
        "float16",
        "--max-model-len",
        "2048",
        "--max-num-seqs",
        "8",
        "--load-format",
        "auto",
    ]
    if chunked_prefill:
        common_args.append("--enable-chunked-prefill")
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
        common_args.extend(["--hf-overrides", hf_overrides])

    ep_env = {
        "VLLM_TEST_ENABLE_EP": "1",
    }

    ep_args = [
        *common_args,
        "--tensor-parallel-size",
        str(tp_size),
        "--distributed-executor-backend",
        distributed_backend,
    ]

    # compare without expert parallelism
    tp_env = {
        "VLLM_TEST_ENABLE_EP": "0",
    }

    tp_args = [
        *common_args,
        "--tensor-parallel-size",
        str(tp_size),
        "--distributed-executor-backend",
        "mp",
    ]

    try:
        compare_two_settings(
            model_name,
            ep_args,
            tp_args,
            ep_env,
            tp_env,
            method=method,
            max_wait_seconds=360,
        )
    except Exception:
        raise