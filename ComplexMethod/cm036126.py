def test_v1_generation_is_deterministic_across_batch_sizes_with_needle(
    backend,
):
    """
    Ensures that the same request (the 'needle' prompt) yields identical output
    whether run alone (bs=1) or mixed into a larger batch (e.g., bs=64),
    using the high-level v1 LLM() API only (no manual batching).

    Strategy:
    - Create a single LLM engine configured for the larger batch limit (N).
    - Compute a baseline output for the needle prompt when it is run alone.
    - For many trials, generate a mixed batch (size N) where the needle appears
      at a random position among random filler prompts using the same engine.
    - Track how many trials match vs mismatch, and report totals at the end.
      The test fails if any mismatches occur, but we still dump pass/fail
      counts.

    Notes:
    - Use seeded stochastic sampling with a fixed seed to test determinism.
    - Outputs are intentionally longer and sampled at higher temperature/top_p
      to produce a more random-sounding phrase, yet remain deterministic by
      seed.
    - Keep max_tokens and max_model_len bounded for speed and memory use.
    """
    seed = int(os.getenv("VLLM_TEST_SEED", "12345"))
    random.seed(seed)

    attention_config = {"backend": backend}
    # Allow overrides from environment (useful for CI tuning)
    # "facebook/opt-125m" is too small, doesn't reliably test determinism
    model = TEST_MODEL
    num_trials = int(os.getenv("VLLM_NEEDLE_TRIALS", "5"))
    max_batch_size = int(os.getenv("VLLM_NEEDLE_BATCH_SIZE", "128"))
    min_random_prompt = int(os.getenv("VLLM_MIN_PROMPT", "1024"))
    max_random_prompt = int(os.getenv("VLLM_MAX_PROMPT", "2048"))
    assert max_batch_size >= 2, "Batch size should be >= 2 to mix needle."

    # Keep GPU memory usage low to avoid startup allocation failures.
    gpu_mem_util = float(os.getenv("VLLM_GPU_MEMORY_UTILIZATION", "0.5"))
    max_model_len = int(os.getenv("VLLM_MAX_MODEL_LEN", "5120"))

    # Sampling parameters: longer outputs with a more random-sounding
    # continuation,but still deterministic due to fixed seed.
    temperature = float(os.getenv("VLLM_NEEDLE_TEMPERATURE", "0.0"))
    top_p = float(os.getenv("VLLM_NEEDLE_TOP_P", "0.95"))
    max_tokens = int(os.getenv("VLLM_NEEDLE_MAX_TOKENS", "128"))

    sampling = SamplingParams(
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
        seed=20240919,
    )

    needle_prompt = "There once was a "

    llm = None
    try:
        llm = LLM_with_max_seqs(
            model=model,
            max_num_seqs=max_batch_size,
            gpu_memory_utilization=gpu_mem_util,
            max_model_len=max_model_len,
            attention_config=attention_config,
        )

        # Baseline generation for the needle prompt alone.
        baseline_out = llm.generate([needle_prompt], sampling)
        assert len(baseline_out) == 1
        assert len(baseline_out[0].outputs) >= 1
        baseline_text = baseline_out[0].outputs[0].text

        mismatches = 0

        for trial in range(num_trials):
            # Create a batch of size `max_batch_size` and insert the needle at
            # a random index
            prompts: list[str] = []
            batch_size = random.randint(max_batch_size // 2, max_batch_size)
            needle_pos = random.randint(0, batch_size - 1)
            for i in range(batch_size):
                if i == needle_pos:
                    prompts.append(needle_prompt)
                else:
                    prompts.append(_random_prompt(min_random_prompt, max_random_prompt))

            # Generate with the same engine but in a larger batch.
            outputs = llm.generate(prompts, sampling)
            # Find the needle output by position
            needle_output = outputs[needle_pos]
            assert needle_output.prompt == needle_prompt
            assert len(needle_output.outputs) >= 1
            text = needle_output.outputs[0].text

            if text != baseline_text:
                print(f"{text}\n\n== Not the same as ==\n\n{baseline_text}\n\n")
                mismatches += 1

        passes = num_trials - mismatches
        # Dump how many passed vs failed
        print(
            f"[determinism] total={num_trials}, passed={passes}, "
            f"failed={mismatches}, max_batch_size={max_batch_size}"
        )

        if mismatches > 0:
            pytest.fail(
                f"Nondeterministic outputs detected: {mismatches} failed out "
                f"of {num_trials} trials (max_batch_size={max_batch_size})."
            )

    finally:
        # Ensure engines are shutdown to free GPU/VRAM across test sessions
        if llm is not None:
            with contextlib.suppress(Exception):
                llm.shutdown()