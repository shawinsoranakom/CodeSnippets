def validate_tensors_metadata(
    desc: str,
    expected: tuple[TensorMeta | None, ...],
    actual: tuple[torch.Tensor | TensorMeta | None, ...],
    *,
    raise_on_mismatch: bool = True,
    warn_on_mismatch: bool = False,
) -> list[str]:
    """Validate metadata for a tuple of tensors element-wise.

    Args:
        desc: Description prefix for error/warning messages.
        expected: Tuple of expected metadata (may include ``None`` for grads).
        actual: Tuple of actual tensors or metadata to compare against.
        raise_on_mismatch: If ``True``, raise on the first mismatch.
        warn_on_mismatch: If ``True``, issue warnings for mismatches.

    Returns:
        Aggregated list of difference strings.

    Raises:
        PipeliningMetadataError: If lengths differ or on mismatch.
    """
    if len(expected) != len(actual):
        msg = f"{desc}: expected {len(expected)} tensors, got {len(actual)}"
        if raise_on_mismatch:
            raise PipeliningMetadataError(msg)
        if warn_on_mismatch:
            warnings.warn(msg, UserWarning, stacklevel=2)
        return [msg]

    all_diffs: list[str] = []
    for i, (exp, act) in enumerate(zip(expected, actual, strict=True)):
        if exp is None and act is None:
            continue
        if exp is None or act is None:
            msg = (
                f"{desc}[{i}]: expected {'None' if exp is None else 'metadata'}, "
                f"got {'None' if act is None else 'metadata'}"
            )
            if raise_on_mismatch:
                raise PipeliningMetadataError(msg)
            if warn_on_mismatch:
                warnings.warn(msg, UserWarning, stacklevel=2)
            all_diffs.append(msg)
            continue
        diffs = validate_metadata(
            f"{desc}[{i}]",
            exp,
            act,
            raise_on_mismatch=raise_on_mismatch,
            warn_on_mismatch=warn_on_mismatch,
        )
        all_diffs.extend(diffs)
    return all_diffs