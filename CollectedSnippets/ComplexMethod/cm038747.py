def benchmark_multimodal_processor(
    args: argparse.Namespace,
) -> dict[str, Any]:
    """
    Run the multimodal processor benchmark.
    """
    from vllm import LLM, SamplingParams

    validate_args(args)

    if args.seed is None:
        args.seed = 0

    engine_args = EngineArgs.from_cli_args(args)
    llm = LLM.from_engine_args(engine_args)

    tokenizer = llm.get_tokenizer()
    requests = get_requests(args, tokenizer)

    assert all(
        llm.llm_engine.model_config.max_model_len
        >= (request.prompt_len + request.expected_output_len)
        for request in requests
    ), (
        "Please ensure that max_model_len is greater than the sum of "
        "prompt_len and expected_output_len for all requests."
    )

    prompts = [request.prompt for request in requests]
    expected_output_lens = [request.expected_output_len for request in requests]

    sampling_params = [
        SamplingParams(
            n=1,
            temperature=0.0,
            max_tokens=output_len,
            detokenize=True,
        )
        for output_len in expected_output_lens
    ]

    selected_percentiles = [
        float(p) for p in getattr(args, "metric_percentiles", "99").split(",")
    ]

    freeze_gc_heap()

    num_warmups = getattr(args, "num_warmups", 0)
    if num_warmups > 0:
        print(f"Processing {num_warmups} warmup requests...")
        # Create a temporary args object for warmup requests
        warmup_args = argparse.Namespace(**vars(args))
        warmup_args.num_prompts = num_warmups
        warmup_args.seed += 1
        warmup_requests = get_requests(warmup_args, tokenizer)
        warmup_prompts = [req.prompt for req in warmup_requests]
        warmup_output_lens = [req.expected_output_len for req in warmup_requests]
        warmup_sampling_params = [
            SamplingParams(max_tokens=output_len) for output_len in warmup_output_lens
        ]
        llm.chat(
            warmup_prompts,
            warmup_sampling_params,
            use_tqdm=not getattr(args, "disable_tqdm", False),
        )

    # Clear stats from warmup requests
    collect_mm_processor_stats(llm.llm_engine)

    print(f"Processing {len(prompts)} requests...")
    start_time = time.perf_counter()

    outputs = llm.chat(
        prompts, sampling_params, use_tqdm=not getattr(args, "disable_tqdm", False)
    )

    end_time = time.perf_counter()
    total_time = end_time - start_time

    mm_stats_by_stage = collect_mm_processor_stats(llm.llm_engine)

    if not any(mm_stats_by_stage.values()):
        print(
            "\n⚠️  Warning: No MM processor stats found in registry.\n"
            "   This may indicate that:\n"
            "   - No multimodal requests were processed\n"
            "   - Stats were already retrieved (registry is cleared after retrieval)\n"
        )

    mm_processor_metrics = calculate_mm_processor_metrics(
        mm_stats_by_stage, selected_percentiles
    )

    completed = len([o for o in outputs if o.finished])
    failed = len(outputs) - completed

    e2el_times = []
    for output in outputs:
        if not output.finished or output.metrics is None:
            continue
        metrics = output.metrics
        # Calculate E2E latency as: TTFT + (last_token_ts - first_token_ts)
        if (
            getattr(metrics, "first_token_latency", None) is not None
            and getattr(metrics, "last_token_ts", None) is not None
            and getattr(metrics, "first_token_ts", None) is not None
        ):
            ttft = metrics.first_token_latency
            # Decode time is the duration between the first and last token generation
            decode_time = max(0.0, metrics.last_token_ts - metrics.first_token_ts)
            e2el_times.append((ttft + decode_time) * 1000)

    if not e2el_times and completed > 0:
        print(
            "\n⚠️  Warning: Detailed end-to-end latency metrics not available.\n"
            "   Falling back to average request latency "
            "(total_time / num_completed_requests).\n"
        )
        avg_time_per_request = total_time / completed
        e2el_times = [avg_time_per_request * 1000] * completed

    if e2el_times:
        mean_e2el_ms = float(np.mean(e2el_times))
        median_e2el_ms = float(np.median(e2el_times))
        std_e2el_ms = float(np.std(e2el_times))
        percentiles_e2el_ms = [
            (p, float(np.percentile(e2el_times, p))) for p in selected_percentiles
        ]
    else:
        mean_e2el_ms = 0.0
        median_e2el_ms = 0.0
        std_e2el_ms = 0.0
        percentiles_e2el_ms = [(p, 0.0) for p in selected_percentiles]

    encoder_summary = {}
    if (
        "num_encoder_calls" in mm_stats_by_stage
        and mm_stats_by_stage["num_encoder_calls"]
    ):
        encoder_calls = mm_stats_by_stage["num_encoder_calls"]
        encoder_summary = {
            "total_encoder_calls": int(sum(encoder_calls)),
            "num_requests_with_encoder_calls": len(encoder_calls),
        }

    benchmark_result = {
        "completed": completed,
        "failed": failed,
        "mean_e2el_ms": mean_e2el_ms,
        "median_e2el_ms": median_e2el_ms,
        "std_e2el_ms": std_e2el_ms,
        "percentiles_e2el_ms": percentiles_e2el_ms,
        "mm_processor_stats": mm_processor_metrics,
        "encoder_summary": encoder_summary,
    }

    return benchmark_result