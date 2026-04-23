def validate_static_arg_grad_correspondence(
    stage_index: int,
    args: tuple[torch.Tensor, ...],
    grads: tuple[torch.Tensor | None, ...],
    is_input: bool,
) -> None:
    """
    Validate the args↔grads contract for static mode.

    Enforces four rules for each (arg, grad) pair:
      1. len(args) must equal len(grads).
      2. If arg.requires_grad is False, grad must be None.
      3. If arg.requires_grad is True and grad is None, emit a warning
         (this is legal at pipeline boundaries but may indicate a bug).
      4. If arg is a DTensor with requires_grad=True and grad is not None,
         grad must also be a DTensor.

    Args:
        stage_index: The stage index for error messages.
        args: Tuple of forward tensors.
        grads: Tuple of gradient tensors (can include None).
        is_input: True for input_args/input_grads, False for output_args/output_grads.

    Raises:
        PipeliningMetadataError: If any hard rule (1, 2, or 4) is violated.
    """
    kind = "input" if is_input else "output"
    args_name = f"{kind}_args"
    grads_name = f"{kind}_grads"

    # Rule 1: lengths must match
    if len(args) != len(grads):
        raise PipeliningMetadataError(
            f"Stage {stage_index}: {grads_name} length ({len(grads)}) does not match "
            f"{args_name} length ({len(args)}). Each forward tensor must have a "
            f"corresponding gradient entry (use None for tensors that don't require grad)."
        )

    for i, (arg, grad) in enumerate(zip(args, grads, strict=True)):
        # Rule 2: no grad for a non-differentiable arg
        if not arg.requires_grad and grad is not None:
            raise PipeliningMetadataError(
                f"Stage {stage_index}: {args_name}[{i}] has requires_grad=False, "
                f"but {grads_name}[{i}] is not None ({type(grad).__name__}). "
                f"Non-differentiable tensors must have None as their gradient entry."
            )

        # Rule 3: missing grad for a differentiable arg (warn, don't raise)
        if arg.requires_grad and grad is None:
            warnings.warn(
                f"Stage {stage_index}: {args_name}[{i}] has requires_grad=True, "
                f"but {grads_name}[{i}] is None. This is legal at pipeline boundaries "
                f"but may indicate a missing gradient.",
                UserWarning,
                stacklevel=2,
            )

        # Rule 4: DTensor arg must have DTensor grad
        if (
            isinstance(arg, DTensor)
            and arg.requires_grad
            and grad is not None
            and not isinstance(grad, DTensor)
        ):
            raise PipeliningMetadataError(
                f"Stage {stage_index}: {args_name}[{i}] is a DTensor with requires_grad=True, "
                f"but {grads_name}[{i}] is {type(grad).__name__}, expected DTensor or None. "
                f"DTensor gradients may have different placements than forward tensors."
            )