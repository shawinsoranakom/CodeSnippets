def is_impure(
    op: Callable,
    *,
    args: tuple[Any, ...] | None = None,
    kwargs: dict[str, Any] | None = None,
    impure_random: bool = True,
) -> bool:
    """
    An operator is impure if it:
    - Mutates its inputs (has a mutable schema)
    - Has nondeterministic/random behavior that mutates RNG state
    - Is explicitly marked as effectful via torch.library._register_effectful_op

    Args:
        op: The operator to check (function, OpOverload, HigherOrderOperator, etc.)
        args: Optional arguments that would be passed to the callable
        kwargs: Optional keyword arguments that would be passed to the callable
        impure_random: Whether to treat random operations as impure (default: True)

    Returns:
        bool: True if the callable has side effects, False otherwise
    """
    # Import here to avoid circular dependencies
    from torch._higher_order_ops.effects import _get_effect
    from torch.fx.node import _side_effectful_functions

    if isinstance(op, torch._ops.OpOverload):
        schema = getattr(op, "_schema", None)
        if schema is not None and schema.is_mutable:
            return True

        if op in _side_effectful_functions:
            return True

        if _get_effect(op) is not None:
            return True

    if isinstance(op, torch._ops.HigherOrderOperator):
        if op in (
            torch.ops.higher_order.auto_functionalized,
            torch.ops.higher_order.auto_functionalized_v2,
        ):
            # Check if the auto-functionalized operator (the first argument) is
            # side-effectful
            if args and len(args) > 0:
                return args[0] in _side_effectful_functions

        if _get_effect(op) is not None:
            return True

        if op in _side_effectful_functions:
            return True

        return False

    # Impure since it mutates RNG state
    if impure_random and getattr(op, "_nondeterministic_seeded", False):
        return True

    # Handle Python random functions that don't have _nondeterministic_seeded
    # but still affect global RNG state (issue #151524)
    # These should be impure regardless of impure_random setting to maintain
    # consistency between eager and compiled execution
    # All random operations are impure to ensure consistent behavior
    # between eager and compiled execution, regardless of generator usage
    if op in _RANDOM_FUNCTIONS:
        return True

    schema = getattr(op, "_schema", None)
    if schema is not None and schema.is_mutable:
        return True

    if op in _side_effectful_functions:
        return True

    return False