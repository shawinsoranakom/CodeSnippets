def analyze_results(
    op_name: str,
    case_names: list[str],
    providers: list[str],
    results: dict[str, dict[str, float]],
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[str]]:
    native_col = "native"
    non_native = [p for p in providers if p != native_col]

    header_cols = ["case"]
    for p in providers:
        header_cols.append(f"{p} (us)")
    for p in non_native:
        header_cols.append(f"{p} speedup")

    detail_rows: list[dict[str, str]] = []
    speedup_data: dict[str, list[tuple[float, str]]] = {p: [] for p in non_native}

    for case_name in case_names:
        timings = results[case_name]
        row: dict[str, str] = {"case": case_name}

        for p in providers:
            val = timings.get(p, float("nan"))
            row[f"{p} (us)"] = f"{val:.2f}" if not math.isnan(val) else "n/a"

        native_us = timings.get(native_col, float("nan"))
        for p in non_native:
            p_us = timings.get(p, float("nan"))
            if not math.isnan(native_us) and not math.isnan(p_us) and p_us > 0:
                speedup = native_us / p_us
                row[f"{p} speedup"] = f"{speedup:.2f}x"
                speedup_data[p].append((speedup, case_name))
            else:
                row[f"{p} speedup"] = "n/a"

        detail_rows.append(row)

    summary_rows: list[dict[str, str]] = []
    for p in non_native:
        entries = speedup_data[p]
        if not entries:
            continue
        speedups = [s for s, _ in entries]
        geomean = math.exp(sum(math.log(s) for s in speedups) / len(speedups))
        best_val, best_case = max(entries)
        worst_val, worst_case = min(entries)
        wins = sum(1 for s in speedups if s > 1.0)
        losses = sum(1 for s in speedups if s < 1.0)
        total = len(speedups)

        print(f"\n{p} vs native ({wins}/{total} faster, {losses}/{total} slower):")
        print(f"  geomean speedup: {geomean:.2f}x")
        print(f"  best:            {best_val:.2f}x  ({best_case})")
        print(f"  worst:           {worst_val:.2f}x  ({worst_case})")

        summary_rows.append(
            {
                "op": op_name,
                "provider": p,
                "geomean_speedup": f"{geomean:.2f}",
                "best_speedup": f"{best_val:.2f}",
                "best_case": best_case,
                "worst_speedup": f"{worst_val:.2f}",
                "worst_case": worst_case,
                "wins": str(wins),
                "losses": str(losses),
                "total": str(total),
            }
        )

    return detail_rows, summary_rows, header_cols