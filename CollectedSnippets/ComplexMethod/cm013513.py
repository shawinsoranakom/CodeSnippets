def _suggest_fixes_for_data_dependent_error_non_strict(
    e: GuardOnDataDependentSymNode,
) -> None:
    """
    Given a raised data-dependent error, add the following to the error message:
    1. the closest user code location that raised the error;
    2. suggested fixes for the error in terms of live variables at that location.
    """

    # walk the stack up from the data-dependent error until a non-torch frame is found
    frame = _find_user_code_frame()
    if frame is not None:
        # add frame info to error message
        _blame_user_code(e, frame)

        # map symbol names reachable via frame locals to their source-level names
        src_map = defaultdict(list)
        for var, val in frame.f_locals.items():
            try:
                tree_leaves_with_path = pytree.tree_leaves_with_path(val)
            except ValueError:
                log.warning(
                    "pytree.tree_leaves_with_path failed for value of type {%s} in local variable {%s}",
                    type(val),
                    var,
                )
                continue
            # figure out how to access any symbol inside `val` through `var`
            for path, leaf in tree_leaves_with_path:
                name = var + pytree.keystr(path)
                if isinstance(leaf, torch.SymInt):
                    src_map[str(leaf.node.expr)].append(name)
                elif isinstance(leaf, torch.Tensor):
                    for i, dim in enumerate(leaf.shape):
                        if isinstance(dim, torch.SymInt):
                            src_map[str(dim.node.expr)].append(f"{name}.shape[{i}]")

        # add suggested torch.check()s based on `src_map` to the error message
        # replacing unbacked symints in the unresolved condition in the error
        if isinstance(e.cond, sympy.logic.boolalg.Boolean):
            _suggest_torch_checks(e, src_map)