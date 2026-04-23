def specialize_symnode(arg: Any) -> Any:
    from .variables import ConstantVariable, LazyVariableTracker, SymNodeVariable

    # Guard and specialize
    if isinstance(arg, LazyVariableTracker) and not arg.is_realized():
        # Find if the arg would be realized as SymNodeVariable later on. If yes,
        # realize it and specialize. Else return the arg.

        source = arg.original_source()
        value = arg.original_value()

        is_symnode_vt = is_torch_sym(value) or (
            not config.specialize_int
            and type(value) is int
            and not is_int_specialization_case(value, source)
        )

        if not is_symnode_vt:
            return arg

    if isinstance(arg, SymNodeVariable):
        return ConstantVariable.create(arg.evaluate_expr())
    return arg