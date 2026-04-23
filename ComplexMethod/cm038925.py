def main():
    set_random_seed(0)
    torch.set_default_device("cuda")
    dtype = torch.bfloat16

    for name, E, N, K, topk, dtype_str, use_fp8, block_shape in MODELS:
        print(f"\n{'=' * 90}")
        print(f"  {name}  (E={E}, N={N}, K={K}, topk={topk})")
        print(f"{'=' * 90}")

        # Try to load tuned config
        block_n = block_shape[0] if block_shape else None
        block_k = block_shape[1] if block_shape else None
        tuned = get_moe_configs(E, N, dtype_str, block_n, block_k)
        has_tuned = tuned is not None
        print(f"  Tuned config available: {has_tuned}")

        hdr = (
            f"{'Batch':>6} | {'Tuned (us)':>11} | {'Old (us)':>11} | "
            f"{'New (us)':>11} | {'New/Old':>8} | {'New/Tuned':>10}"
        )
        print(f"  {hdr}")
        print(f"  {'-' * len(hdr)}")

        for M in BATCH_SIZES:
            old_cfg = old_default_config(M, E, N, K, topk, dtype_str, block_shape)
            new_cfg = get_default_config(M, E, N, K, topk, dtype_str, block_shape)

            if has_tuned:
                tuned_cfg = tuned[min(tuned.keys(), key=lambda x: abs(x - M))]
                t_tuned = benchmark_config(
                    tuned_cfg,
                    M,
                    E,
                    N,
                    K,
                    topk,
                    dtype,
                    use_fp8=use_fp8,
                    block_shape=block_shape,
                )
            else:
                t_tuned = None

            t_old = benchmark_config(
                old_cfg,
                M,
                E,
                N,
                K,
                topk,
                dtype,
                use_fp8=use_fp8,
                block_shape=block_shape,
            )
            t_new = benchmark_config(
                new_cfg,
                M,
                E,
                N,
                K,
                topk,
                dtype,
                use_fp8=use_fp8,
                block_shape=block_shape,
            )

            ratio_new_old = t_new / t_old
            tuned_str = f"{t_tuned:11.2f}" if t_tuned else f"{'N/A':>11}"
            ratio_tuned = f"{t_new / t_tuned:10.2f}x" if t_tuned else f"{'N/A':>10}"
            # flag regressions where new default is >5% slower than old
            marker = " <--" if ratio_new_old > 1.05 else ""

            print(
                f"  {M:>6} | {tuned_str} | {t_old:11.2f} | {t_new:11.2f} "
                f"| {ratio_new_old:7.2f}x | {ratio_tuned}{marker}"
            )