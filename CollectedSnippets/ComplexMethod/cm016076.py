def main():
    """Run benchmark with specified parameters."""
    DATA_SIZE = 99999
    AVG_TIMES = 10
    BATCH_SIZES = [4, 8, 64, 640, 6400, 64000]
    DROP_LAST_OPTIONS = [True, False]

    results = []

    # Set up samplers here, ensure right args are passed in
    baselineSampler = BatchSampler
    testSampler = NewBatchSampler

    for batch_size in BATCH_SIZES:
        for drop_last in DROP_LAST_OPTIONS:
            print(f"Benchmarking with batch_size={batch_size}, drop_last={drop_last}")

            # Benchmark baselineSampler
            original_times = []
            for _ in range(AVG_TIMES):
                start = time.perf_counter()
                for _ in baselineSampler(
                    sampler=SequentialSampler(range(DATA_SIZE)),
                    batch_size=batch_size,
                    drop_last=drop_last,
                ):
                    pass
                end = time.perf_counter()
                original_times.append(end - start)
                time.sleep(0.1)

            original_avg = float(np.mean(original_times))

            # Benchmark testSampler
            new_times = []
            for _ in range(AVG_TIMES):
                start = time.perf_counter()
                for _ in testSampler(
                    sampler=SequentialSampler(range(DATA_SIZE)),
                    batch_size=batch_size,
                    drop_last=drop_last,
                ):
                    pass
                end = time.perf_counter()
                new_times.append(end - start)
                time.sleep(0.1)  # Small delay to reduce system load

            new_avg = float(np.mean(new_times))

            # Calculate speedup
            if original_avg > 0 and new_avg > 0:
                speedup = (original_avg - new_avg) / original_avg * 100
                speedup_str = f"{speedup:.2f}%"
            else:
                speedup_str = "N/A"

            print(f"Speedup: {speedup_str}\n")

            results.append(
                [
                    batch_size,
                    drop_last,
                    f"{original_avg:.4f}",
                    f"{new_avg:.4f}",
                    speedup_str,
                ]
            )

    # Print results in a table
    headers = ["Batch Size", "Drop Last", "Original (s)", "New (s)", "Speedup"]
    print("\nBenchmark Results:")
    print(tabulate(results, headers=headers, tablefmt="grid"))