def prepare_results_with_speedups(results_dict):
    """Prepare results with speedup calculations based on dynamic baseline selection."""
    prepared_results = []

    # Determine the fastest baseline for each operation type
    def get_fastest_baseline(op_name, results_dict):
        """Get the fastest baseline between standard and native_compiled versions."""
        if "fp8_quant" in op_name:
            candidates = [
                "standard_allreduce_rmsnorm_fp8_quant",
                "standard_allreduce_rmsnorm_fp8_quant_native_compiled",
            ]
        elif "fp4_quant" in op_name:
            candidates = [
                "standard_allreduce_rmsnorm_fp4_quant",
                "standard_allreduce_rmsnorm_fp4_quant_native_compiled",
            ]
        else:
            candidates = [
                "standard_allreduce_rmsnorm",
                "standard_allreduce_rmsnorm_native_compiled",
            ]

        # Find the fastest among available candidates
        fastest_time = float("inf")
        fastest_baseline = None

        for candidate in candidates:
            if (
                candidate in results_dict
                and results_dict[candidate] != float("inf")
                and results_dict[candidate] < fastest_time
            ):
                fastest_time = results_dict[candidate]
                fastest_baseline = candidate

        return fastest_baseline

    # Create dynamic baseline mapping
    dynamic_baseline_mapping = {}
    for op_name in results_dict:
        if (
            op_name.startswith("flashinfer_")
            or op_name.startswith("standard_")
            and not op_name.endswith("_native_compiled")
        ):
            dynamic_baseline_mapping[op_name] = get_fastest_baseline(
                op_name, results_dict
            )

    for op_name, time_ms in results_dict.items():
        if time_ms == float("inf"):
            speedup_str = "FAILED"
            time_str = "FAILED"
        else:
            time_str = f"{time_ms:.3f}"
            # Find the appropriate baseline for this operation
            baseline_op = dynamic_baseline_mapping.get(op_name)
            if baseline_op and baseline_op in results_dict:
                baseline_time = results_dict[baseline_op]
                if baseline_time != float("inf") and baseline_time > 0:
                    speedup = baseline_time / time_ms
                    speedup_str = f"{speedup:.2f}x"
                else:
                    speedup_str = "N/A"
            else:
                # For baseline operations, determine if this is the fastest baseline
                if op_name.endswith("_native_compiled") or (
                    op_name.startswith("standard_")
                    and not op_name.endswith("_native_compiled")
                ):
                    fastest_baseline = get_fastest_baseline(op_name, results_dict)
                    if fastest_baseline == op_name:
                        speedup_str = "baseline"
                    else:
                        if fastest_baseline and fastest_baseline in results_dict:
                            baseline_time = results_dict[fastest_baseline]
                            if baseline_time != float("inf") and baseline_time > 0:
                                speedup = baseline_time / time_ms
                                speedup_str = f"{speedup:.2f}x"
                            else:
                                speedup_str = "N/A"
                        else:
                            speedup_str = "N/A"
                else:
                    speedup_str = "N/A"

        prepared_results.append(
            {
                "operation": op_name,
                "time_ms": time_ms,
                "time_str": time_str,
                "speedup_str": speedup_str,
            }
        )

    return prepared_results