def _check_ground_truth(
    result: Any,
) -> torch.Tensor | list[torch.Tensor] | None:
    """Validate an op result is suitable as ground truth.

    Returns the ground truth tensor(s) or None if the result should be skipped.
    """
    if isinstance(result, (list, tuple)):
        if not all(isinstance(t, torch.Tensor) for t in result):
            return None
        gt = list(result)
    elif isinstance(result, torch.Tensor):
        gt = result
    else:
        return None

    first_gt = gt[0] if isinstance(gt, list) else gt
    if first_gt.numel() == 0:
        return None
    if (first_gt == 0).all():
        return None
    if first_gt.isnan().all():
        return None
    return gt