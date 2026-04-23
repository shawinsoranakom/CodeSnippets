def compare_operator(
    op_name: str,
    device: str = "cpu",
    dtype: torch.dtype = torch.float32,
    world_size: int = 2,
    max_samples: int | None = None,
    verbose: bool = False,
    incorrect_only: bool = False,
    allow_composite: bool = False,
) -> ComparisonStats:
    """
    Compare DTensor's sharding rules against ground truth for an operator.

    Args:
        op_name: Name of the operator to test
        device: Device to run on
        dtype: Data type for tensors
        world_size: Simulated world size
        max_samples: Maximum number of samples to test per OpInfo
        verbose: Print detailed output
        incorrect_only: If True, only test DTensor's claimed rules for correctness.
            Skips search for missing rules (much faster).
        allow_composite: If True, validate each supported aten op individually for
            samples that decompose into multiple aten calls. Default (False)
            skips samples where the OpInfo doesn't map 1:1 to a single aten op.
    """
    if op_name in SKIP_OPS:
        return ComparisonStats()

    opinfos = get_opinfo_by_name(op_name)

    stats = ComparisonStats()

    if not allow_composite:
        aten_op = _discover_aten_op(opinfos, device, dtype)
        if aten_op is None or not _has_dtensor_support(aten_op):
            if verbose:
                print(f"  ATEN_OP_MAP: {op_name} -> {aten_op} [no_support]")
            stats.no_dtensor_support = True
            return stats
        if verbose:
            print(f"  ATEN_OP_MAP: {op_name} -> {aten_op} [supported]")

    total_samples = 0
    total_combinations = 0
    skip_reasons: dict[str, int] = defaultdict(int)

    for opinfo in opinfos:
        variant = opinfo.variant_test_name
        if variant and verbose:
            print(f"\n  OpInfo variant: {variant}")

        op = opinfo.op

        try:
            samples = list(opinfo.sample_inputs(device, dtype))
        except Exception as e:
            if verbose:
                print(f"    Error generating samples: {e}")
            continue

        if max_samples:
            samples = samples[:max_samples]

        for sample_idx, sample in enumerate(samples):
            # Check that SampleInput has tensor inputs and no zero-sized tensors
            sample_tensors = extract_tensors_from_sample(sample)
            if len(sample_tensors) == 0:
                skip_reasons["no tensor inputs"] += 1
                continue
            if any(0 in t.shape for _, t in sample_tensors):
                skip_reasons["zero-sized tensor"] += 1
                continue

            # Capture all aten ops dispatched for this sample
            capture = get_aten_op_for_sample(op, sample, opinfo.name)
            if capture.best_match is None:
                skip_reasons["no aten op captured"] += 1
                continue

            # Count supported aten ops in the capture
            supported_ops = [
                (func, args, kwargs, result)
                for func, args, kwargs, result in capture.all_ops
                if _has_dtensor_support(func)
            ]
            num_supported = len(supported_ops)

            if allow_composite:
                # Validate each supported aten op individually
                if num_supported == 0:
                    skip_reasons["no supported aten ops"] += 1
                    continue

                for func, args, kwargs, result in supported_ops:
                    gt = _check_ground_truth(result)
                    if gt is None:
                        skip_reasons["non-tensor/degenerate aten output"] += 1
                        continue
                    n_samples, n_combos = _validate_aten_op_for_sample(
                        func,
                        args,
                        kwargs,
                        gt,
                        world_size,
                        incorrect_only,
                        verbose,
                        sample_idx,
                        variant,
                        stats,
                        sample,
                    )
                    total_samples += n_samples
                    total_combinations += n_combos
            else:
                # Default: only validate samples with a single supported aten op
                if num_supported != 1:
                    skip_reasons["non-1:1 aten mapping"] += 1
                    continue

                func, args, kwargs, result = supported_ops[0]
                gt = _check_ground_truth(result)
                if gt is None:
                    skip_reasons["non-tensor/degenerate aten output"] += 1
                    continue

                n_samples, n_combos = _validate_aten_op_for_sample(
                    func,
                    args,
                    kwargs,
                    gt,
                    world_size,
                    incorrect_only,
                    verbose,
                    sample_idx,
                    variant,
                    stats,
                    sample,
                )
                total_samples += n_samples
                total_combinations += n_combos

    stats.total_samples = total_samples
    stats.total_combinations = total_combinations
    stats.skip_reasons = dict(skip_reasons)

    # In allow_composite mode, check DTensor support after processing
    if allow_composite and total_samples == 0 and not skip_reasons:
        stats.no_dtensor_support = True

    return stats