def _create_partial_input(
    tensor: torch.Tensor,
    placement: Partial,
    world_size: int,
    tensor_idx: int = 0,
    mask_shift: int = 0,
) -> LocalTensor:
    """
    Create a LocalTensor with values that reduce to the original tensor.

    Uses asymmetric splits to avoid coincidental matches when combining
    different Partial types.

    For each placement combination, it creates local tensors that would
    reduce to the original (e.g., for P(sum), splits values across ranks so
    they sum back), runs the op on those local tensors, wraps the output as
    a DTensor, redistributes to Replicate, and compares against ground
    truth.

    The main challenge is avoiding false positives where a rule appears
    valid on a specific input but is actually incorrect. Several techniques
    are used:

    Asymmetric splits for P(sum)/P(avg): instead of splitting evenly
    (tensor/2 per rank), uses a 60/40 ratio (varied by tensor index) so
    that ops which are not truly linear don't accidentally produce
    matching outputs.

    Sign-varying offsets for P(sum)/P(avg): adds an offset that
    alternates sign across elements, so local tensors have mixed positive
    and negative values. Without this, proportional splits preserve the
    sign pattern of the original tensor, causing non-linear ops like abs
    to falsely validate P(sum)->P(sum).

    Distinct magnitudes for P(min) vs P(max): P(min) offsets non-holding
    ranks by +(range*2+1) while P(max) offsets by -(range*2+1), where
    range is the tensor's value range. Using adaptive offsets that exceed
    the value range ensures that index-returning ops (argmin/argmax)
    produce different results on different ranks, correctly rejecting
    P(min)/P(max) inputs for those ops. Using different signs for min vs
    max prevents accidental cancellation when both appear in the same
    combination.

    Alternating rank ownership for P(min)/P(max): a multi-dimensional
    checkerboard mask (sum of coordinates mod 2) controls which rank holds
    the true value vs the offset value. Unlike a flat-index mask which can
    have uniform parity along an even-stride dimension, the checkerboard
    guarantees alternation along EVERY dimension. The mask_shift parameter
    allows re-validation with the complementary mask to catch ops where
    the result coincidentally matches.

    """
    reduce_op = placement.reduce_op
    local_tensors: dict[int, torch.Tensor] = {}

    if reduce_op in ("sum", "avg"):
        base_ratio = 0.6 + 0.1 * (tensor_idx % 3)

        # See docstring above: "Sign-varying offsets"
        flat = tensor.flatten()
        offset_mag = flat.abs() + 1.0
        signs = torch.ones_like(flat)
        # Use checkerboard mask so offset sign alternates in every dimension,
        # not just along flat index (which can be uniform along even-stride dims).
        signs[_checkerboard_mask(tensor, tensor_idx, mask_shift)] = -1.0
        offset = (offset_mag * signs).reshape(tensor.shape)

        scale = world_size if reduce_op == "avg" else 1
        for r in range(world_size):
            if r == 0:
                local_tensors[r] = tensor.clone() * base_ratio * scale + offset
            else:
                local_tensors[r] = tensor.clone() * (
                    (1 - base_ratio) / (world_size - 1)
                ) * scale - offset / (world_size - 1)

    elif reduce_op == "min":
        # See docstring above: "Distinct Magnitudes" and "Alternating Rank Ownership"
        flat = tensor.flatten()
        # Offset must exceed the tensor's value range so that the mask pattern
        # determines argmin/argmax, not the original values.
        value_range = (flat.max() - flat.min()).item()
        min_offset = value_range * 2 + 1
        mask = _checkerboard_mask(tensor, tensor_idx, mask_shift)
        for r in range(world_size):
            if r == 0:
                r_offset = torch.where(
                    mask, torch.zeros_like(flat), torch.full_like(flat, min_offset)
                )
            else:
                r_offset = torch.where(
                    mask, torch.full_like(flat, min_offset), torch.zeros_like(flat)
                )
            local_tensors[r] = (flat + r_offset).reshape(tensor.shape)

    elif reduce_op == "max":
        # See docstring above: "Distinct Magnitudes" and "Alternating Rank Ownership"
        flat = tensor.flatten()
        value_range = (flat.max() - flat.min()).item()
        max_offset = -(value_range * 2 + 1)
        mask = _checkerboard_mask(tensor, tensor_idx, mask_shift)
        for r in range(world_size):
            if r == 0:
                r_offset = torch.where(
                    mask, torch.zeros_like(flat), torch.full_like(flat, max_offset)
                )
            else:
                r_offset = torch.where(
                    mask, torch.full_like(flat, max_offset), torch.zeros_like(flat)
                )
            local_tensors[r] = (flat + r_offset).reshape(tensor.shape)

    else:
        for r in range(world_size):
            local_tensors[r] = tensor.clone()

    # pyrefly: ignore [bad-argument-type, bad-argument-count]
    return LocalTensor(local_tensors)