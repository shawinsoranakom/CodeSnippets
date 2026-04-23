def pickle_guards_state(
    state: GuardsState,
    builder: GuardBuilder,
) -> bytes:
    buf = io.BytesIO()
    empty_values = {}
    missing_values = {}
    guard_tree_values = builder.guard_tree_values

    leaves = pytree.tree_leaves(state.output_graph.local_scope)
    for leaf in leaves:
        if inspect.ismethod(leaf) and hasattr(leaf, "__self__"):
            base = leaf.__self__
            if id(base) not in guard_tree_values:
                try:
                    type(base).__new__(type(base))
                    empty_values[id(base)] = base
                except:  # noqa: E722
                    pass
        elif id(leaf) not in guard_tree_values:
            # TODO See if we have lift this branch as the first one.
            # Prune more objects in pytree hierarchy.
            missing_values[id(leaf)] = leaf
    pickler = GuardsStatePickler(guard_tree_values, empty_values, missing_values, buf)

    if all(
        torch.compiler.keep_portable_guards_unsafe(
            [
                make_guard_filter_entry(guard, builder)
                for guard in state.output_graph.guards
            ]
        )
    ):
        # Prune more values in AOT precompile when complex pickling structure is not needed.
        state.output_graph.guard_on_key_order = set()
        state.output_graph.global_scope = {}

    try:
        pickler.dump(state)
    except AttributeError as e:
        raise torch._dynamo.exc.PackageError(str(e)) from e
    return buf.getvalue()