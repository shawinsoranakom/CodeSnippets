def _validate_aten_op_for_sample(
    aten_op: OpOverload,
    captured_args: tuple[Any, ...],
    captured_kwargs: dict[str, Any],
    ground_truth: torch.Tensor | list[torch.Tensor],
    world_size: int,
    incorrect_only: bool,
    verbose: bool,
    sample_idx: int,
    variant: str,
    stats: ComparisonStats,
    sample: SampleInput | None = None,
) -> tuple[int, int]:
    """Validate a single aten op with captured args against ground truth.

    Shared logic used by both default (1:1) and allow_composite modes in
    compare_operator. Returns (samples_counted, combinations_counted).
    """
    tensors = extract_tensors_from_args(captured_args, captured_kwargs)
    if not tensors:
        return 0, 0
    if any(0 in t.shape for _, t in tensors):
        return 0, 0

    input_shapes = tuple(t.shape for _, t in tensors)
    gt_list = ground_truth if isinstance(ground_truth, list) else [ground_truth]
    output_shapes = tuple(tuple(gt.shape) for gt in gt_list)
    n_outputs = len(gt_list)
    first_gt = gt_list[0]

    scalar_args = tuple(a for a in captured_args if not isinstance(a, torch.Tensor))
    scalar_kwargs = {
        k: v for k, v in captured_kwargs.items() if not isinstance(v, torch.Tensor)
    }

    mitigations = _prepare_aten_mitigations(aten_op, captured_args, captured_kwargs)

    input_placement_options = [
        get_1d_input_placements_for_tensor(t, include_partial=True) for _, t in tensors
    ]
    output_placement_options = get_1d_output_placements_for_tensor(first_gt)

    dtensor_rules = _query_dtensor_rules(
        aten_op,
        tensors,
        captured_args,
        captured_kwargs,
        input_shapes,
        output_shapes,
        world_size,
        verbose,
    )

    ground_truth_valid: set[ComboKey] = set()
    total_combinations = 0

    tensor_device = tensors[0][1].device.type if tensors else "cpu"
    with LocalTensorMode(frozenset(range(world_size))):
        mesh = init_device_mesh(tensor_device, (world_size,))

        if incorrect_only:
            combinations_to_test = []
            for combo_key in dtensor_rules:
                input_plc_strs, output_plc_strs = combo_key
                input_plcs_list: list[Placement] = []
                all_valid = True
                for s in input_plc_strs:
                    p = parse_placement(s)
                    if p is None:
                        all_valid = False
                        break
                    input_plcs_list.append(p)
                output_plcs_list: list[Placement] = []
                for s in output_plc_strs:
                    p = parse_placement(s)
                    if p is None:
                        all_valid = False
                        break
                    output_plcs_list.append(p)
                if not all_valid:
                    continue
                combinations_to_test.append(
                    (
                        tuple(input_plcs_list),
                        tuple(output_plcs_list),
                        combo_key,
                    )
                )
        else:
            combinations_to_test = []
            for input_placements in itertools.product(*input_placement_options):
                if is_fully_replicated(input_placements):
                    continue
                for output_placement in output_placement_options:
                    output_placements = tuple(
                        output_placement for _ in range(n_outputs)
                    )
                    combo_key = (
                        tuple(str(p) for p in input_placements),
                        tuple(str(p) for p in output_placements),
                    )
                    combinations_to_test.append(
                        (input_placements, output_placements, combo_key)
                    )

        untestable: set[ComboKey] = set()

        for (
            input_placements,
            output_placements,
            combo_key,
        ) in combinations_to_test:
            total_combinations += 1
            is_valid = _validate_aten_with_mitigations(
                aten_op,
                captured_args,
                captured_kwargs,
                input_placements,
                output_placements,
                ground_truth,
                world_size,
                mesh,
                mitigations,
            )

            if is_valid is None:
                normalized_key = normalize_combo_key(
                    combo_key, input_shapes, output_shapes
                )
                untestable.add(normalized_key)
            elif is_valid:
                normalized_key = normalize_combo_key(
                    combo_key, input_shapes, output_shapes
                )
                if not is_fully_replicated(
                    tuple(parse_placement(p) or Replicate() for p in normalized_key[0])
                ):
                    ground_truth_valid.add(normalized_key)

    _compare_rules(
        ground_truth_valid,
        dtensor_rules,
        input_shapes,
        output_shapes,
        sample_idx,
        scalar_args,
        scalar_kwargs,
        aten_op,
        variant,
        stats,
        sample,
        untestable,
    )

    if verbose:
        print(f"      Sample {sample_idx} [{aten_op}]: shapes={input_shapes}")
        print(f"        Ground truth valid: {len(ground_truth_valid)}")
        print(f"        DTensor rules: {len(dtensor_rules)}")

    return 1, total_combinations