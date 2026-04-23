def run_multi_process_fuzzer(
    num_processes: int | None = None,
    seed_start: int = 0,
    seed_count: int = 100,
    verbose: bool = False,
    template: str = "default",
    supported_ops: str | None = None,
) -> None:
    """
    Run the multi-process fuzzer.

    Args:
        num_processes: Number of worker processes to use
        seed_start: Starting seed value (inclusive)
        seed_count: Number of seeds to run
        verbose: Whether to print detailed output
        template: The template to use for code generation
        supported_ops: Comma-separated ops string with optional weights
    """
    seeds = list(range(seed_start, seed_start + seed_count))

    persist_print(f"🚀 Starting multi-process fuzzer with {num_processes} processes")
    persist_print(
        f"📊 Processing seeds {seed_start} to {seed_start + seed_count - 1} ({len(seeds)} total)"
    )
    persist_print(
        f"🔧 Command template: python fuzzer.py --seed {{seed}} --template {template}"
    )
    persist_print("=" * 60)

    start_time = time.time()
    results: list[FuzzerResult] = []
    successful_count = 0
    failed_count = 0
    ignored_count = 0
    ignored_seeds = []
    ignored_pattern_counts: dict[int, int] = dict.fromkeys(
        range(len(IGNORE_PATTERNS)), 0
    )

    try:
        # Use multiprocessing Pool to distribute work
        with mp.Pool(processes=num_processes) as pool:
            # Submit all seeds to the process pool
            future_results = []
            for seed in seeds:
                future = pool.apply_async(
                    run_fuzzer_with_seed, (seed, template, supported_ops)
                )
                future_results.append(future)

            # Set up progress bar
            if HAS_TQDM:
                from tqdm import tqdm  # Import the real tqdm here

                pbar = tqdm(
                    total=len(seeds),
                    desc="Processing seeds",
                    file=sys.stdout,
                    bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}] ✅/❌/❓={postfix}",
                    dynamic_ncols=True,
                )
                pbar.set_postfix_str(
                    f"{successful_count}/{failed_count}/{ignored_count} | throughput: 0.00 seeds/hr"
                )

                def write_func(msg):
                    # pyrefly: ignore [missing-attribute]
                    pbar.write(msg)
            else:
                persist_print("Progress: (install tqdm for better progress bar)")
                pbar = None
                write_func = persist_print

            # Collect results as they complete
            for i, future in enumerate(future_results):
                try:
                    result: FuzzerResult = future.get()
                    results.append(result)

                    if result.ignored_pattern_idx != -1:
                        ignored_seeds.append(result.seed)
                        ignored_pattern_counts[result.ignored_pattern_idx] += 1
                        ignored_count += 1

                    # Only increment failed_count if not ignored
                    if result.success:
                        successful_count += 1
                    elif result.ignored_pattern_idx == -1:
                        failed_count += 1

                    elapsed = time.time() - start_time
                    throughput = (i + 1) / (elapsed / 3600)

                    # Update progress bar
                    if HAS_TQDM and pbar:
                        pbar.set_postfix_str(
                            f"{successful_count}/{failed_count}/{ignored_count} | throughput: {throughput:.2f} seeds/hr"
                        )
                        pbar.update(1)
                    else:
                        status_emoji = "✅" if result.success else "❌"
                        ignored_text = (
                            " (IGNORED)" if result.ignored_pattern_idx != -1 else ""
                        )
                        persist_print(
                            f"Completed {i + 1}/{len(seeds)} - Seed {result.seed}: {status_emoji}{ignored_text}"
                        )

                    # Unified output handling
                    if not result.success and result.ignored_pattern_idx == -1:
                        handle_result_output(
                            label="❌ FAILURE",
                            seed=result.seed,
                            duration=result.duration,
                            output=result.output,
                            ignored=False,
                            verbose=verbose,
                            write_func=write_func,
                        )
                    elif not result.success and result.ignored_pattern_idx != -1:
                        if verbose:
                            handle_result_output(
                                label="🚫 IGNORED",
                                seed=result.seed,
                                duration=result.duration,
                                output=result.output,
                                ignored=True,
                                verbose=verbose,
                                write_func=write_func,
                            )
                    elif verbose:
                        handle_result_output(
                            label="✅ SUCCESS",
                            seed=result.seed,
                            duration=result.duration,
                            output=result.output,
                            ignored=(result.ignored_pattern_idx != -1),
                            verbose=verbose,
                            write_func=write_func,
                        )

                except Exception as e:
                    failed_count += 1
                    if HAS_TQDM and pbar:
                        pbar.set_postfix_str(f"{successful_count}/{failed_count}")
                        pbar.update(1)
                        pbar.write(f"❌ POOL ERROR - Seed {seeds[i]}: {str(e)}")
                    else:
                        persist_print(
                            f"Completed {i + 1}/{len(seeds)} - Seed {seeds[i]}: ❌ POOL ERROR"
                        )
                        persist_print(f"❌ POOL ERROR - Seed {seeds[i]}: {str(e)}")
                    results.append(
                        FuzzerResult(
                            seeds[i], False, f"Pool error: {str(e)}", 0.0, -1, {}
                        )
                    )

            # Close progress bar
            if HAS_TQDM and pbar:
                pbar.close()
    except KeyboardInterrupt:
        persist_print("\n🛑 Interrupted by user (Ctrl+C)")
        # Print summary up to this point
        total_time = time.time() - start_time
        persist_print("=" * 60)
        persist_print("📈 SUMMARY (partial, interrupted)")
        persist_print("=" * 60)

        successful = [res for res in results if res.success]
        # Only count as failed if not ignored
        failed = [
            res for res in results if not res.success and res.ignored_pattern_idx == -1
        ]
        ignored = [res for res in results if res.ignored_pattern_idx != -1]

        persist_print(
            f"✅ Successful: {len(successful)}/{len(results)} ({(len(successful) / len(results) * 100 if results else 0):.1f}%)"
        )
        persist_print(
            f"❌ Failed:     {len(failed)}/{len(results)} ({(len(failed) / len(results) * 100 if results else 0):.1f}%)"
        )
        persist_print(f"⏱️  Total time: {total_time:.2f}s")
        if results:
            persist_print(
                f"⚡ Throughput: {(len(results) / (total_time / 3600)):.2f} seeds/hr"
                if total_time > 0
                else "⚡ Throughput: N/A"
            )
        if failed:
            persist_print(f"\n❌ Failed seeds: {[res.seed for res in failed]}")
        if successful:
            persist_print(f"✅ Successful seeds: {[res.seed for res in successful]}")
            avg_success_time = sum(res.duration for res in successful) / len(successful)
            persist_print(f"⚡ Avg time for successful runs: {avg_success_time:.2f}s")
        if ignored:
            persist_print(f"\n🚫 Ignored seeds: {[res.seed for res in ignored]}")
            # Print ignore pattern stats
            persist_print("\n🚫 Ignored pattern statistics:")
            total_ignored = len(ignored)
            for idx, pattern in enumerate(IGNORE_PATTERNS):
                count = ignored_pattern_counts[idx]
                percent = (count / total_ignored * 100) if total_ignored else 0
                persist_print(
                    f"  Pattern {idx}: {pattern.pattern!r} - {count} ({percent:.1f}%)"
                )

        # Aggregate and print operation distribution
        _print_operation_distribution(results)

        sys.exit(130)

    total_time = time.time() - start_time

    # Print summary
    persist_print("=" * 60)
    persist_print("📈 SUMMARY")
    persist_print("=" * 60)

    successful = [res for res in results if res.success]
    # Only count as failed if not ignored
    failed = [
        res for res in results if not res.success and res.ignored_pattern_idx == -1
    ]
    ignored = [res for res in results if res.ignored_pattern_idx != -1]

    persist_print(
        f"✅ Successful: {len(successful)}/{len(results)} ({len(successful) / len(results) * 100:.1f}%)"
    )
    persist_print(
        f"❌ Failed:     {len(failed)}/{len(results)} ({len(failed) / len(results) * 100:.1f}%)"
    )
    persist_print(f"⏱️  Total time: {total_time:.2f}s")
    persist_print(
        f"⚡ Throughput: {(len(results) / (total_time / 3600)):.2f} seeds/hr"
        if total_time > 0
        else "⚡ Throughput: N/A"
    )

    if failed:
        persist_print(f"\n❌ Failed seeds: {[res.seed for res in failed]}")

    if successful:
        persist_print(f"✅ Successful seeds: {[res.seed for res in successful]}")
        avg_success_time = sum(res.duration for res in successful) / len(successful)
        persist_print(f"⚡ Avg time for successful runs: {avg_success_time:.2f}s")

    if ignored:
        persist_print(f"\n🚫 Ignored seeds: {[res.seed for res in ignored]}")
        # Print ignore pattern stats
        persist_print("\n🚫 Ignored pattern statistics:")
        total_ignored = len(ignored)
        for idx, pattern in enumerate(IGNORE_PATTERNS):
            count = ignored_pattern_counts[idx]
            percent = (count / total_ignored * 100) if total_ignored else 0
            persist_print(
                f"  Pattern {idx}: {pattern.pattern!r} - {count} ({percent:.1f}%)"
            )

    # Aggregate and print operation distribution
    _print_operation_distribution(results)