def dispatch_torch_function(
    tx: "InstructionTranslator",
    fn: VariableTracker,
    args: Iterable[Any],
    kwargs: dict[str, Any],
) -> Any:
    """Gathers all args that are TensorWithTFOverrideVariable and dispatches based on the ordering in _get_overloaded_args"""

    all_args = _get_all_args(args, kwargs)
    overloaded_args = _get_overloaded_args(
        [arg for arg in all_args if has_torch_function(arg)],
        _get_subclass_type,
    )

    types = TupleVariable([_get_subclass_type_var(tx, arg) for arg in overloaded_args])

    if tx.symbolic_torch_function_state.in_torch_function_mode():
        res = tx.symbolic_torch_function_state.call_torch_function_mode(
            tx, fn, types, args, kwargs
        )
        if not res.is_constant_match(NotImplemented):
            return res

    for arg in overloaded_args:
        res = arg.call_torch_function(
            tx,
            fn,
            types,
            args,
            kwargs,
        )

        if not res.is_constant_match(NotImplemented):
            tx.output.torch_function_subclass_inlined = True
            return res

    unimplemented(
        gb_type="All __torch_function__ overrides returned NotImplemented due to TypeError from user code",
        context=f"{fn=}, {args=}, {kwargs=}",
        explanation=f"All __torch_function__ overrides for function {fn} returned NotImplemented",
        hints=[
            *graph_break_hints.USER_ERROR,
        ],
    )