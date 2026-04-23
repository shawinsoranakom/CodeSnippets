def gen_functionalization_definition(
    selector: SelectiveBuilder,
    # Note: Ideally this code should never have to look at NativeFunction
    # (and instead only need to operate on grouped NativeFunctions).
    # The only reason currently is because we need to emit direct dispatch registrations
    # For CompositeImplicitAutograd operators, which are potentially ungrouped.
    g: NativeFunction | NativeFunctionsGroup | NativeFunctionsViewGroup,
) -> list[str]:
    # Don't generate kernels in mobile build
    if not selector.include_all_operators:
        return []

    if isinstance(g, NativeFunctionsViewGroup):
        # Case 1: emit view -> view_copy kernels for the functionalization pass
        view_defs = []
        if not g.composite:
            # invariant: NativeFunctionsViewGroup's always have a view_copy operator
            # if the view is not composite (implicit autograd)
            if g.view_copy is None:
                raise AssertionError(
                    f"Expected view_copy to be non-None: {dataclass_repr(g, indent=1)}"
                )
            view_defs.append(emit_view_functionalization_body(g, view_inplace=False))
            if g.view_inplace is not None:
                view_defs.append(emit_view_functionalization_body(g, view_inplace=True))
        return view_defs
    elif isinstance(g, NativeFunction):
        # Invariant: all mutable operators that we need to handle in functionalization
        # should have been properly grouped up.
        # TODO: The below ops all have "problematic" schemas that prevent them from
        # getting functionalized. Instead of bending over backwards to get things to work,
        # I think we should either:
        # (1) fix their schemas (BC-breaking)
        # (2) hand-write their functionalization kernels
        if (
            str(g.func.name) not in MUTABLE_OPS_NOT_USING_FUNCTIONALIZATION
            and str(g.func.name.name) not in MUTABLE_OPS_NOT_USING_FUNCTIONALIZATION
        ):
            if not (
                g.has_composite_implicit_autograd_kernel or not modifies_arguments(g)
            ):
                raise AssertionError(
                    f"Expected composite implicit autograd kernel or non-modifying function: {g.func}"
                )
        return []
    else:
        # Case 2: emit inplace -> out-of-place kernels for the functionalization pass
        mutation_defs = []
        mutation_defs.append(emit_inplace_functionalization_body(g.out, g))
        if g.inplace is not None:
            mutation_defs.append(emit_inplace_functionalization_body(g.inplace, g))
        if g.mutable is not None:
            mutation_defs.append(emit_inplace_functionalization_body(g.mutable, g))
        return mutation_defs
    return []