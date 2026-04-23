def rotate_checkpoints(
    output_dir: str,
    save_total_limit: int | None = None,
    best_model_checkpoint: str | None = None,
    use_mtime: bool = False,
    checkpoint_prefix: str = PREFIX_CHECKPOINT_DIR,
) -> None:
    """
    Delete older checkpoints, keeping at most `save_total_limit`.

    Always preserves the most recent checkpoint and the best model checkpoint (if provided).

    Args:
        output_dir (`str`):
            The directory containing the checkpoints.
        save_total_limit (`int`, *optional*):
            Maximum number of checkpoints to keep. No deletion if `None` or <= 0.
        best_model_checkpoint (`str`, *optional*):
            Path to best checkpoint (will always be preserved).
        use_mtime (`bool`, *optional*, defaults to `False`):
            Whether to sort by modification time instead of step number.
        checkpoint_prefix (`str`, *optional*, defaults to `"checkpoint"`):
            The prefix used for checkpoint directory names.
    """
    if save_total_limit is None or save_total_limit <= 0:
        return

    checkpoints = sort_checkpoints(output_dir, checkpoint_prefix, use_mtime)
    if len(checkpoints) <= save_total_limit:
        return

    # Checkpoints that must not be deleted
    protected = {checkpoints[-1]}  # most recent, for resuming
    if best_model_checkpoint is not None:
        protected.add(str(Path(best_model_checkpoint)))

    # Delete oldest non-protected checkpoints until we have save_total_limit left
    num_to_keep = max(save_total_limit, len(protected))
    remaining = len(checkpoints)
    for checkpoint in checkpoints:
        if remaining <= num_to_keep:
            break
        if checkpoint not in protected:
            shutil.rmtree(checkpoint, ignore_errors=True)
            remaining -= 1