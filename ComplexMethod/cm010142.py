def make_fake_inputs(
    nn_module,
    args,
    kwargs,
    dynamic_shapes,
    prefer_deferred_runtime_asserts_over_guards=False,
):
    """
    Given an nn module, example inputs, and constraints, return a new fake mode,
    fake inputs created in that mode whose dynamic shape dimensions are constrained
    by the given ranges, and sources for pairs of dynamic shape dimensions that are
    constrained to be equal.
    """
    # TODO(avik): refactor Dynamo to avoid duplication of the following code
    # between non-strict and strict.
    # Specifically, here (non-strict) we do the following pre-tracing steps:
    #   - Fakify inputs.
    #   - Process input shape equalities.
    # In strict, these steps are spread across multiple files:
    #   - output_graph.py fakifies inputs.
    #   - [post-tracing] guards.py processes input shape equalities.
    import torch._functorch.config as _config

    # Map ints to a wrapper structure to help us mark it as dynamic, if it is
    # dynamic. We will unwrap ints in fakify later.
    args, kwargs = pytree.tree_map_only(int, lambda a: _IntWrapper(a), (args, kwargs))

    combined_args = _combine_args(nn_module, args, kwargs)
    _check_dynamic_shapes(combined_args, dynamic_shapes)
    constraints = _process_dynamic_shapes(combined_args, dynamic_shapes)
    t_constraints: dict[int, dict[int, Constraint]] = defaultdict(dict)
    for constraint in constraints:
        t_constraints[constraint.t_id][constraint.dim] = constraint

    context = torch._guards.TracingContext.try_get()
    if context is not None:
        # This occurs when we are exporting within dynamo. There already exists
        # a toplevel TracingContext with a fake mode, so we do not want to
        # create another fake mode.
        fake_mode = context.fake_mode
        if fake_mode is None:
            raise AssertionError("context.fake_mode must not be None")
    else:
        if isinstance(nn_module.forward, functools.partial):
            # functools handles nesting by itself, no need to recurse
            code = nn_module.forward.func.__code__
        elif (
            sys.version_info >= (3, 14)
            and (fwd := getattr(nn_module.forward, "__func__", None))
            and isinstance(fwd, functools.partial)
        ):
            # functools.partial is now a method descriptor:
            # https://docs.python.org/3/whatsnew/3.14.html#changes-in-the-python-api
            code = fwd.func.__code__
        else:
            code = nn_module.forward.__code__
        co_fields = {
            "co_name": code.co_name,
            "co_filename": code.co_filename,
            "co_firstlineno": code.co_firstlineno,
        }
        with _config.patch(fake_tensor_allow_unsafe_data_ptr_access=False):
            fake_mode = FakeTensorMode(
                shape_env=ShapeEnv(
                    tracked_fakes=[],
                    co_fields=co_fields,
                    prefer_deferred_runtime_asserts_over_guards=prefer_deferred_runtime_asserts_over_guards,
                    trace_asserts=True,
                ),
                allow_non_fake_inputs=True,
                export=True,
            )
    if fake_mode.shape_env is None or fake_mode.shape_env.tracked_fakes is None:
        raise ValueError(
            "Detected fake_mode does not have a shape_env with tracked fakes. "
            "If you constructed the module under a FakeTensorMode, "
            "please initialize it like: FakeTensorMode(shape_env=ShapeEnv(tracked_fakes=[]))"
        )

    with fake_mode:
        original_signature = inspect.signature(nn_module.forward)
        sources: dict[tuple[int, int], list[Source]] = defaultdict(list)
        sourced_prefixes = make_sourced_prefixes(nn_module, args, kwargs)
        fake_args, fake_kwargs = tree_map_with_path(
            lambda kp, val: fakify(
                fake_mode,
                kp,
                val,
                t_constraints,
                sources,
                sourced_prefixes=sourced_prefixes,
            ),
            (args, kwargs),
        )

        names: dict[str, tuple[int, int]] = {}
        source_pairs: list[tuple[Source, Source]] = []
        derived_equalities: list[tuple[Source, Source | Symbol, Callable]] = []
        phantom_symbols: dict[str, Symbol] = {}
        relaxed_sources: set[Source] = set()
        for constraint in constraints:
            torch.export.dynamic_shapes._process_equalities(
                constraint,
                lambda t_id, dim: sources[(t_id, dim)],
                fake_mode.shape_env,
                names,
                source_pairs,
                derived_equalities,
                phantom_symbols,
                relaxed_sources,
            )

        equalities_inputs = EqualityConstraint(
            source_pairs=source_pairs,
            derived_equalities=derived_equalities,
            phantom_symbols=list(phantom_symbols.values()),
            relaxed_sources=relaxed_sources,
            warn_only=False,
        )
        return (
            fake_mode,
            fake_args,
            fake_kwargs,
            equalities_inputs,
            original_signature,
            dynamic_shapes,
        )