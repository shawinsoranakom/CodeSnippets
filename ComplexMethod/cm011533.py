def _compare_rules(
    ground_truth_valid: set[ComboKey],
    dtensor_rules: set[ComboKey],
    input_shapes: tuple[tuple[int, ...], ...],
    output_shapes: tuple[tuple[int, ...], ...],
    sample_idx: int,
    scalar_args: tuple[Any, ...],
    scalar_kwargs: dict[str, Any],
    aten_op: OpOverload | None,
    variant: str,
    stats: ComparisonStats,
    sample: SampleInput | None = None,
    untestable: set[ComboKey] | None = None,
) -> None:
    """Compare ground truth valid rules against DTensor claimed rules, updating stats."""
    if not dtensor_rules:
        return
    if untestable is None:
        untestable = set()

    _assert_keys_normalized(ground_truth_valid, input_shapes, output_shapes)
    _assert_keys_normalized(dtensor_rules, input_shapes, output_shapes)

    op_str = str(aten_op)
    for combo_key in ground_truth_valid:
        if combo_key in dtensor_rules:
            stats.true_positives += 1
            stats.true_positives_by_op[op_str] = (
                stats.true_positives_by_op.get(op_str, 0) + 1
            )
        elif combo_key not in untestable:
            stats.false_negatives.append(
                Discrepancy(
                    input_placements=combo_key[0],
                    output_placements=combo_key[1],
                    sample_idx=sample_idx,
                    input_shapes=input_shapes,
                    discrepancy_type="false_negative",
                    scalar_args=scalar_args,
                    scalar_kwargs=scalar_kwargs,
                    aten_op=aten_op,
                    variant=variant,
                    sample=sample,
                )
            )

    for combo_key in dtensor_rules:
        if combo_key not in ground_truth_valid and combo_key not in untestable:
            stats.false_positives.append(
                Discrepancy(
                    input_placements=combo_key[0],
                    output_placements=combo_key[1],
                    sample_idx=sample_idx,
                    input_shapes=input_shapes,
                    discrepancy_type="false_positive",
                    scalar_args=scalar_args,
                    scalar_kwargs=scalar_kwargs,
                    aten_op=aten_op,
                    variant=variant,
                    sample=sample,
                )
            )