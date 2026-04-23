def run_benchmark_with_batch_invariant(
    model: str,
    tp_size: int,
    max_batch_size: int,
    num_trials: int,
    min_prompt: int,
    max_prompt: int,
    max_tokens: int,
    temperature: float,
    gpu_mem_util: float,
    max_model_len: int,
    backend: str,
    batch_invariant: bool,
    seed: int = 12345,
) -> dict:
    """
    Run the benchmark with the specified configuration.

    Returns a dict with timing and throughput metrics.
    """
    random.seed(seed)

    # Set environment variables
    if batch_invariant:
        os.environ["VLLM_BATCH_INVARIANT"] = "1"
    else:
        os.environ["VLLM_BATCH_INVARIANT"] = "0"

    print(f"\n{'=' * 80}")
    print(f"BENCHMARK: VLLM_BATCH_INVARIANT={int(batch_invariant)}")
    print(f"  Model: {model}")
    print(f"  TP Size: {tp_size}")
    print(f"  Backend: {backend}")
    print(f"  Max Batch Size: {max_batch_size}")
    print(f"  Trials: {num_trials}")
    print(f"  Max Tokens: {max_tokens}")
    print(f"{'=' * 80}\n")

    sampling = SamplingParams(
        temperature=temperature,
        top_p=0.95,
        max_tokens=max_tokens,
        seed=20240919,
    )

    needle_prompt = "There once was a "

    llm = None
    try:
        # Create LLM engine
        start_init = time.perf_counter()
        llm = LLM(
            model=model,
            max_num_seqs=max_batch_size,
            gpu_memory_utilization=gpu_mem_util,
            max_model_len=max_model_len,
            dtype="bfloat16",
            tensor_parallel_size=tp_size,
            attention_config={"backend": backend},
            enable_prefix_caching=False,
        )
        init_time = time.perf_counter() - start_init
        print(f"Engine initialization time: {init_time:.2f}s\n")

        # Generate baseline
        print("Generating baseline (warmup)...")
        baseline_out = llm.generate([needle_prompt], sampling)
        assert len(baseline_out) == 1
        baseline_text = baseline_out[0].outputs[0].text
        print(f"Baseline output: '{baseline_text[:50]}...'\n")

        # Run trials and measure timing
        trial_times: list[float] = []
        total_tokens = 0
        total_prompts = 0

        for trial in range(num_trials):
            # Create a batch
            prompts: list[str] = []
            batch_size = random.randint(max_batch_size // 2, max_batch_size)
            needle_pos = random.randint(0, batch_size - 1)
            for i in range(batch_size):
                if i == needle_pos:
                    prompts.append(needle_prompt)
                else:
                    prompts.append(_random_prompt(min_prompt, max_prompt))

            # Measure time for this trial
            start_time = time.perf_counter()
            outputs = llm.generate(prompts, sampling)
            trial_time = time.perf_counter() - start_time

            trial_times.append(trial_time)
            total_prompts += len(prompts)

            # Count tokens
            for output in outputs:
                if output.outputs:
                    total_tokens += len(output.outputs[0].token_ids)

            print(
                f"Trial {trial + 1}/{num_trials}: "
                f"batch_size={batch_size}, "
                f"time={trial_time:.2f}s"
            )

            # Verify needle output still matches
            needle_output = outputs[needle_pos]
            assert needle_output.prompt == needle_prompt

        # Compute statistics
        avg_time = sum(trial_times) / len(trial_times)
        min_time = min(trial_times)
        max_time = max(trial_times)
        throughput = total_tokens / sum(trial_times)
        prompts_per_sec = total_prompts / sum(trial_times)

        print(f"\n{'=' * 80}")
        print("RESULTS:")
        print(f"  Average time per trial: {avg_time:.2f}s")
        print(f"  Min time: {min_time:.2f}s")
        print(f"  Max time: {max_time:.2f}s")
        print(f"  Total tokens generated: {total_tokens}")
        print(f"  Total prompts processed: {total_prompts}")
        print(f"  Throughput: {throughput:.2f} tokens/s")
        print(f"  Prompts/s: {prompts_per_sec:.2f}")
        print(f"{'=' * 80}\n")

        return {
            "init_time": init_time,
            "avg_time": avg_time,
            "min_time": min_time,
            "max_time": max_time,
            "total_tokens": total_tokens,
            "total_prompts": total_prompts,
            "throughput": throughput,
            "prompts_per_sec": prompts_per_sec,
            "trial_times": trial_times,
        }

    finally:
        # Cleanup
        if llm is not None:
            with contextlib.suppress(Exception):
                llm.shutdown()