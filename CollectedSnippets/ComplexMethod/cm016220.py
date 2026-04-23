def run_until_failure(
    num_processes: int | None = None,
    verbose: bool = False,
    template: str = "default",
    supported_ops: str | None = None,
) -> None:
    """
    Run the multi-process fuzzer with a random starting seed, iterating until a failure is found.

    Args:
        num_processes: Number of worker processes to use
        verbose: Whether to print detailed output
        template: The template to use for code generation
        supported_ops: Comma-separated ops string with optional weights

    Returns:
        Exits with non-zero code when a failure is found
    """
    import random

    # Pick a random seed to start from
    initial_seed = random.randint(0, 2**31 - 1)

    persist_print(
        f"🎲 Starting continuous fuzzing with random initial seed: {initial_seed}"
    )
    persist_print(f"🚀 Using {num_processes} processes")
    persist_print(
        f"🔧 Command template: python fuzzer.py --seed {{seed}} --template {template}"
    )
    persist_print("🎯 Running until first failure is found...")
    persist_print("=" * 60)

    start_time = time.time()
    current_seed = initial_seed
    total_successful = 0
    total_ignored = 0
    batch_size = 100  # Process seeds in batches of 100

    try:
        while True:
            # Process a batch of seeds
            seeds = list(range(current_seed, current_seed + batch_size))

            with mp.Pool(processes=num_processes) as pool:
                future_results = []
                for seed in seeds:
                    future = pool.apply_async(
                        run_fuzzer_with_seed, (seed, template, supported_ops)
                    )
                    future_results.append((seed, future))

                # Set up progress bar for this batch
                if HAS_TQDM:
                    from tqdm import tqdm

                    pbar = tqdm(
                        total=len(seeds),
                        desc=f"Batch starting at seed {current_seed}",
                        file=sys.stdout,
                        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}] ✅/🚫={postfix}",
                        dynamic_ncols=True,
                    )
                    pbar.set_postfix_str(f"{total_successful}/{total_ignored}")

                    def write_func(msg):
                        # pyrefly: ignore [missing-attribute]
                        pbar.write(msg)
                else:
                    pbar = None

                # Collect results as they complete
                for seed, future in future_results:
                    result: FuzzerResult = future.get()

                    if result.ignored_pattern_idx != -1:
                        total_ignored += 1

                    if result.success:
                        total_successful += 1
                    elif result.ignored_pattern_idx == -1:
                        # Found a failure that is not ignored!
                        if HAS_TQDM and pbar:
                            pbar.close()

                        elapsed = time.time() - start_time
                        persist_print("\n" + "=" * 60)
                        persist_print("🎯 FAILURE FOUND!")
                        persist_print("=" * 60)
                        persist_print(f"❌ Failing seed: {result.seed}")
                        persist_print(
                            f"⏱️  Duration for this seed: {result.duration:.2f}s"
                        )
                        persist_print(f"⏱️  Total time elapsed: {elapsed:.2f}s")
                        persist_print(f"✅ Successful seeds tested: {total_successful}")
                        persist_print(f"🚫 Ignored seeds: {total_ignored}")
                        persist_print(
                            f"📊 Total seeds tested: {total_successful + total_ignored + 1}"
                        )
                        persist_print("\n💥 Failure output:")
                        persist_print("-" * 60)
                        print_output_lines(result.output, persist_print)
                        persist_print("-" * 60)
                        persist_print(
                            f"\n🔄 Reproduce with: python fuzzer.py --seed {result.seed} --template {template}"
                        )

                        # Exit with non-zero code
                        sys.exit(1)

                    # Update progress bar
                    if HAS_TQDM and pbar:
                        pbar.set_postfix_str(f"{total_successful}/{total_ignored}")
                        pbar.update(1)
                    elif verbose:
                        status_emoji = "✅" if result.success else "🚫"
                        persist_print(f"Seed {result.seed}: {status_emoji}")

                # Close progress bar for this batch
                if HAS_TQDM and pbar:
                    pbar.close()

            # Move to next batch
            current_seed += batch_size

    except KeyboardInterrupt:
        persist_print("\n🛑 Interrupted by user (Ctrl+C)")
        elapsed = time.time() - start_time
        persist_print("=" * 60)
        persist_print("📈 SUMMARY (interrupted)")
        persist_print("=" * 60)
        persist_print(f"⏱️  Total time: {elapsed:.2f}s")
        persist_print(f"✅ Successful seeds: {total_successful}")
        persist_print(f"🚫 Ignored seeds: {total_ignored}")
        persist_print(f"📊 Total seeds tested: {total_successful + total_ignored}")
        persist_print(
            f"⚡ Throughput: {((total_successful + total_ignored) / (elapsed / 3600)):.2f} seeds/hr"
        )
        sys.exit(130)