def run_benchmark(dtype: torch.dtype, dtype_name: str):
    """Run benchmark for a specific dtype."""
    torch.set_default_device("cuda")

    # Batch sizes to test (powers of 2 from 32 to 65536)
    batch_sizes = [32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536]

    print("=" * 80)
    print("Benchmark: torch.cat vs direct copy for MLA k_nope/k_pe concatenation")
    print("=" * 80)
    print(
        f"Tensor shapes: k_nope=[B, {NUM_HEADS}, {QK_NOPE_HEAD_DIM}], "
        f"k_pe=[B, 1, {PE_DIM}]"
    )
    print(f"dtype: {dtype_name}")
    print()
    print(
        f"{'Batch Size':>12} | {'cat (ms)':>10} | {'direct (ms)':>12} | "
        f"{'Speedup':>8} | {'Reduction':>10}"
    )
    print("-" * 70)

    results = []
    for batch_size in batch_sizes:
        # Create input tensors (generate in float32 then convert for FP8 compatibility)
        k_nope = torch.randn(
            batch_size, NUM_HEADS, QK_NOPE_HEAD_DIM, dtype=torch.float32, device="cuda"
        ).to(dtype)
        k_pe = torch.randn(
            batch_size, 1, PE_DIM, dtype=torch.float32, device="cuda"
        ).to(dtype)

        # Benchmark both methods
        cat_time = benchmark_method(cat_method, k_nope, k_pe)
        direct_time = benchmark_method(direct_copy_method, k_nope, k_pe)

        speedup = cat_time / direct_time
        reduction = (1 - direct_time / cat_time) * 100

        results.append((batch_size, cat_time, direct_time, speedup, reduction))

        print(
            f"{batch_size:>12} | {cat_time:>10.3f} | {direct_time:>12.3f} | "
            f"{speedup:>7.2f}x | {reduction:>9.1f}%"
        )

    print("=" * 80)

    # Summary statistics
    speedups = [r[3] for r in results]
    print("\nSpeedup summary:")
    print(f"  Min:  {min(speedups):.2f}x")
    print(f"  Max:  {max(speedups):.2f}x")
    print(f"  Mean: {sum(speedups) / len(speedups):.2f}x")

    # Find crossover point
    crossover_batch = None
    for batch_size, _, _, speedup, _ in results:
        if speedup >= 1.0:
            crossover_batch = batch_size
            break

    print("\nConclusion:")
    if crossover_batch:
        print(f"  - Direct copy becomes beneficial at batch size >= {crossover_batch}")
    # Filter for large batches (>= 512 which is typical for prefill)
    large_batch_speedups = [r[3] for r in results if r[0] >= 512]
    if large_batch_speedups:
        avg_large = sum(large_batch_speedups) / len(large_batch_speedups)
        print(f"  - For batch sizes >= 512: avg speedup = {avg_large:.2f}x")
    print("  - MLA prefill typically uses large batches, so optimization is effective")

    return results