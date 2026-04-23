def _validate_aten_with_mitigations(
    aten_op: OpOverload,
    captured_args: tuple[Any, ...],
    captured_kwargs: dict[str, Any],
    input_placements: tuple[Placement, ...],
    output_placements: tuple[Placement, ...],
    ground_truth: torch.Tensor | list[torch.Tensor],
    world_size: int,
    mesh: DeviceMesh,
    mitigations: _AtenFalsePositiveMitigations,
) -> bool | None:
    """Validate an aten-level combination with false positive mitigations.

    Returns True (valid), False (invalid), or None (untestable).
    """
    combo: PlacementCombination = (input_placements, output_placements)
    is_valid, _ = validate_aten_combination(
        aten_op,
        captured_args,
        captured_kwargs,
        ground_truth,
        combo,
        world_size,
        mesh,
    )
    if is_valid is None:
        return None

    if is_valid and has_any_partial(input_placements, output_placements):
        is_valid, _ = validate_aten_combination(
            aten_op,
            captured_args,
            captured_kwargs,
            ground_truth,
            combo,
            world_size,
            mesh,
            mask_shift=1,
        )

    if (
        is_valid
        and mitigations.negated_args is not None
        and has_pmin_pmax(input_placements, output_placements)
    ):
        if mitigations.negated_kwargs is None:
            raise AssertionError("negated_kwargs must not be None")
        if mitigations.negated_ground_truth is None:
            raise AssertionError("negated_ground_truth must not be None")
        is_valid, _ = validate_aten_combination(
            aten_op,
            mitigations.negated_args,
            mitigations.negated_kwargs,
            mitigations.negated_ground_truth,
            combo,
            world_size,
            mesh,
        )

    return is_valid