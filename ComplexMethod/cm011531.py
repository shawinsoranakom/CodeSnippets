def _validate_with_mitigations(
    op: Callable[..., Any],
    sample: SampleInput,
    tensors: list[tuple[str, torch.Tensor]],
    input_placements: tuple[Placement, ...],
    output_placements: tuple[Placement, ...],
    ground_truth: torch.Tensor | list[torch.Tensor],
    world_size: int,
    mesh: DeviceMesh,
    mitigations: _FalsePositiveMitigations,
) -> bool | None:
    """Validate a combination, including false positive mitigation re-checks.

    Returns True (valid), False (invalid), or None (untestable).
    """
    combo: PlacementCombination = (input_placements, output_placements)
    is_valid, _ = validate_combination(
        op, sample, tensors, combo, ground_truth, world_size, mesh
    )
    if is_valid is None:
        return None

    # Flipped-mask mitigation: the checkerboard mask that controls offset
    # signs (for P(sum)/P(avg)) or rank ownership (for P(min)/P(max)) is
    # deterministic per tensor_idx. Re-validate with the complementary mask
    # to catch index-returning ops (argmin/argmax) where the result
    # coincidentally matches because the dominant value happens to land on
    # a position where both mask orientations preserve argmin/argmax.
    if is_valid and has_any_partial(input_placements, output_placements):
        is_valid, _ = validate_combination(
            op,
            sample,
            tensors,
            combo,
            ground_truth,
            world_size,
            mesh,
            mask_shift=1,
        )

    if (
        is_valid
        and mitigations.negated_sample
        and has_pmin_pmax(input_placements, output_placements)
    ):
        if mitigations.negated_tensors is None:
            raise AssertionError("negated_tensors is None")
        if mitigations.negated_ground_truth is None:
            raise AssertionError("negated_ground_truth is None")
        is_valid, _ = validate_combination(
            op,
            mitigations.negated_sample,
            mitigations.negated_tensors,
            combo,
            mitigations.negated_ground_truth,
            world_size,
            mesh,
        )

    if (
        is_valid
        and mitigations.non_rounded_sample
        and has_any_partial(input_placements, output_placements)
    ):
        if mitigations.non_rounded_ground_truth is None:
            raise AssertionError("non_rounded_ground_truth is None")
        is_valid, _ = validate_combination(
            op,
            mitigations.non_rounded_sample,
            tensors,
            combo,
            mitigations.non_rounded_ground_truth,
            world_size,
            mesh,
        )

    if (
        is_valid
        and mitigations.non_rounded_negated_sample
        and has_pmin_pmax(input_placements, output_placements)
    ):
        if mitigations.non_rounded_negated_tensors is None:
            raise AssertionError("non_rounded_negated_tensors is None")
        if mitigations.non_rounded_negated_ground_truth is None:
            raise AssertionError("non_rounded_negated_ground_truth is None")
        is_valid, _ = validate_combination(
            op,
            mitigations.non_rounded_negated_sample,
            mitigations.non_rounded_negated_tensors,
            combo,
            mitigations.non_rounded_negated_ground_truth,
            world_size,
            mesh,
        )

    return is_valid