def print_comparison(all_results):
        print(f"\n{'=' * 80}", flush=True)
        print("COMPARISON", flush=True)
        print(f"{'=' * 80}", flush=True)
        print(
            f"  {'model':<40s} {'backed_ms':>10s} {'unbacked_ms':>11s} {'diff':>8s}",
            flush=True,
        )
        print(f"  {'-' * 40} {'-' * 10} {'-' * 11} {'-' * 8}", flush=True)
        for name, modes in all_results.items():
            b_ms = modes.get("backed_ms")
            u_ms = modes.get("unbacked_ms")
            if b_ms is not None and u_ms is not None:
                ms_diff_pct = (u_ms - b_ms) / b_ms * 100
                print(
                    f"  {name:<40s} {b_ms:>10.3f} {u_ms:>11.3f} {ms_diff_pct:>+7.1f}%",
                    flush=True,
                )
            elif b_ms is not None:
                print(
                    f"  {name:<40s} {b_ms:>10.3f} {'N/A':>11s} {'N/A':>8s}", flush=True
                )
            elif u_ms is not None:
                print(
                    f"  {name:<40s} {'N/A':>10s} {u_ms:>11.3f} {'N/A':>8s}", flush=True
                )
            else:
                backed = (
                    "FAILED" if "backed" not in modes else f"{modes['backed']:.3f}x"
                )
                unbacked = (
                    "FAILED" if "unbacked" not in modes else f"{modes['unbacked']:.3f}x"
                )
                print(
                    f"  {name:<40s} {backed:>10s} {unbacked:>11s} {'N/A':>8s}",
                    flush=True,
                )
        print(f"{'=' * 80}", flush=True)