def _get_codegen(
    in_spec: pytree.TreeSpec,
    out_spec: pytree.TreeSpec | None,
    forward_arg_names: list[str] | None = None,
) -> _PyTreeCodeGen:
    """
    Create the codegen for the graph module based on the in/out specs
    """
    if forward_arg_names:
        names = forward_arg_names
    elif (
        in_spec.type is tuple
        and in_spec.num_children == 2
        and in_spec.child(0).type is tuple
        and in_spec.child(1).type is dict
    ):
        # if in_spec contains the args (tuple) and kwargs (dict)
        names = [f"arg_{i}" for i in range(in_spec.child(0).num_children)]
        # add kwarg names
        names.extend(in_spec.child(1).context)
    else:
        names = [f"arg_{i}" for i in range(in_spec.num_children)]

    return _PyTreeCodeGen(
        _PyTreeInfo(
            names,
            in_spec,
            out_spec,
        )
    )