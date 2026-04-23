def sort_checkpoints(
    output_dir: str,
    checkpoint_prefix: str = PREFIX_CHECKPOINT_DIR,
    use_mtime: bool = False,
    best_model_checkpoint: str | None = None,
) -> list[str]:
    """
    Return checkpoint directories sorted by step number (oldest first).

    Args:
        output_dir (`str`):
            The directory containing the checkpoints.
        checkpoint_prefix (`str`, *optional*, defaults to `"checkpoint"`):
            The prefix used for checkpoint directory names.
        use_mtime (`bool`, *optional*, defaults to `False`):
            Whether to sort by modification time instead of step number.
        best_model_checkpoint (`str`, *optional*):
            If provided, this checkpoint is moved to second-to-last position to protect
            it from deletion while keeping the most recent checkpoint last for resuming.

    Returns:
        `list[str]`: Sorted list of checkpoint directory paths (oldest first).
    """
    glob_checkpoints = [str(x) for x in Path(output_dir).glob(f"{checkpoint_prefix}-*") if os.path.isdir(x)]

    ordering_and_checkpoint_path = []
    for path in glob_checkpoints:
        if use_mtime:
            ordering_and_checkpoint_path.append((os.path.getmtime(path), path))
        else:
            regex_match = re.match(f".*{checkpoint_prefix}-([0-9]+)", path)
            if regex_match is not None and regex_match.groups() is not None:
                ordering_and_checkpoint_path.append((int(regex_match.groups()[0]), path))

    checkpoints_sorted = sorted(ordering_and_checkpoint_path)

    # mtime is not reliable on some filesystems (e.g., cloud fuse filesystems)
    # so we check if the mtime is fake and fall back to numerical ordering
    if use_mtime and len(checkpoints_sorted) > 1:
        mtime_diff = checkpoints_sorted[-1][0] - checkpoints_sorted[0][0]
        if mtime_diff < 1.0:
            logger.warning_once("mtime may not be reliable on this filesystem, falling back to numerical ordering")
            return sort_checkpoints(
                output_dir, checkpoint_prefix, use_mtime=False, best_model_checkpoint=best_model_checkpoint
            )

    checkpoints_sorted = [path for _, path in checkpoints_sorted]

    # Move best_model_checkpoint to second-to-last position to protect it from deletion
    # while keeping the most recent checkpoint at the end for resuming training.
    if best_model_checkpoint is not None:
        best_model_checkpoint = str(Path(best_model_checkpoint))
        if best_model_checkpoint in checkpoints_sorted and checkpoints_sorted[-1] != best_model_checkpoint:
            most_recent = checkpoints_sorted[-1]
            checkpoints_sorted = [c for c in checkpoints_sorted if c not in {best_model_checkpoint, most_recent}]
            checkpoints_sorted += [best_model_checkpoint, most_recent]

    return checkpoints_sorted