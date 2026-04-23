def _run_compare_backed_unbacked(runner, args):
    """Run backed and unbacked per-model, alternating, and compare speedup."""
    import re
    import subprocess

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

    # Build base command, stripping --compare-backed-unbacked, --only, --filter and their values
    # Handles both space-separated (--filter VALUE) and equals-separated (--filter=VALUE) forms
    filtered = []
    skip_next = False
    for a in sys.argv:
        if a == "--compare-backed-unbacked":
            continue
        if skip_next:
            skip_next = False
            continue
        if a == "--only" or a.startswith("--only="):
            if "=" not in a:
                skip_next = True
            continue
        if a == "--filter" or a.startswith("--filter="):
            if "=" not in a:
                skip_next = True
            continue
        filtered.append(a)
    base_cmd = [sys.executable, "-B"] + filtered

    # Get model list from runner
    runner.args = args
    args.filter = args.filter or [r"."]
    args.exclude = args.exclude or [r"^$"]
    args.exclude_exact = args.exclude_exact or []
    models = list(runner.iter_model_names(args))

    if args.only:
        models = [args.only]

    all_results = {}
    for model in models:
        print(f"\n--- {model} ---", flush=True)
        for mode, flag in [
            ("backed", "--dynamic-batch-only"),
            ("unbacked", "--unbacked-batch-only"),
        ]:
            cmd = base_cmd + ["--only", model, flag, "--_print-latency-ms"]
            print(f"  {mode}...", end=" ", flush=True)
            try:
                proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )
                stdout, stderr = proc.communicate(timeout=600)
            except subprocess.TimeoutExpired:
                proc.kill()
                print("TIMEOUT", flush=True)
                continue
            except Exception as e:
                print(f"ERROR ({e})", flush=True)
                continue

            speedup_match = re.search(r"(\d+\.\d+)x", stdout)
            latency_match = re.search(r"([\d.]+) ms, ([\d.]+) ms,", stdout)
            if speedup_match:
                speedup = float(speedup_match.group(1))
                eager_ms = float(latency_match.group(1)) if latency_match else None
                compiled_ms = float(latency_match.group(2)) if latency_match else None
                extra = ""
                if eager_ms and compiled_ms:
                    extra = f" (eager={eager_ms:.3f} ms, compiled={compiled_ms:.3f} ms)"
                print(f"{speedup:.3f}x{extra}", flush=True)
                if model not in all_results:
                    all_results[model] = {}
                all_results[model][mode] = speedup
                if eager_ms is not None:
                    all_results[model][f"{mode}_eager_ms"] = eager_ms
                if compiled_ms is not None:
                    all_results[model][f"{mode}_ms"] = compiled_ms
            else:
                err_match = re.search(
                    r"(Error|Exception|Traceback).*", stdout + stderr, re.IGNORECASE
                )
                if err_match:
                    print("FAILED", flush=True)
                else:
                    print("SKIP", flush=True)

        # Print running diff for this model
        if (
            model in all_results
            and "backed_ms" in all_results[model]
            and "unbacked_ms" in all_results[model]
        ):
            b_ms = all_results[model]["backed_ms"]
            u_ms = all_results[model]["unbacked_ms"]
            ms_diff_pct = (u_ms - b_ms) / b_ms * 100
            print(
                f"  => diff: {ms_diff_pct:+.1f}% ({b_ms:.3f} ms vs {u_ms:.3f} ms)",
                flush=True,
            )
        elif (
            model in all_results
            and "backed" in all_results[model]
            and "unbacked" in all_results[model]
        ):
            b = all_results[model]["backed"]
            u = all_results[model]["unbacked"]
            diff_pct = (u - b) / b * 100
            print(f"  => diff: {diff_pct:+.1f}% (ratio-based, no ms data)", flush=True)

    print_comparison(all_results)