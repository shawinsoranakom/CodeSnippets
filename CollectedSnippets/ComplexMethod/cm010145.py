def make_constraints(
    fake_mode: FakeTensorMode,
    gm: torch.fx.GraphModule,
    combined_args: dict[str, Any],
    dynamic_shapes: dict[str, Any] | tuple[Any] | list[Any] | None,
    num_lifted_inputs: int,
):
    """
    Given a fake mode's shape env and user-specified dynamic shapes,
    return the resulting range constraints and equality constraints.

    Additional args:
        num_lifted_inputs: the number of non-user-input placeholder nodes in the graph
        (used only to enumerate the user-input nodes)
    """

    shape_env = fake_mode.shape_env
    if shape_env is None:
        raise AssertionError("fake_mode.shape_env must not be None")
    inline_constraints = gm.meta.get("inline_constraints", [])
    range_constraints = defaultdict(lambda: ValueRanges(0, int_oo)) | inline_constraints
    if not dynamic_shapes:
        return dict(range_constraints)

    # clean up dynamic markers from tensors
    flat_paths, flat_args = zip(*pytree.tree_flatten_with_path(combined_args)[0])
    for arg in flat_args:
        if isinstance(arg, torch.Tensor):
            _clean_dynamic_markers(arg)

    # get individual dynamic shapes spec for each input
    if not isinstance(dynamic_shapes, dict):
        if not isinstance(dynamic_shapes, (tuple, list)):
            raise AssertionError(
                f"expected dict, tuple, or list for dynamic_shapes, got {type(dynamic_shapes)}"
            )
        combined_args = type(dynamic_shapes)(combined_args.values())  # type: ignore[assignment, misc]
    flat_dynamic_shapes = _flatten_dynamic_shapes(combined_args, dynamic_shapes)

    # check number of shapes vs. number of inputs
    num_placeholders = [node.op == "placeholder" for node in gm.graph.nodes].count(True)
    if len(flat_dynamic_shapes) != num_placeholders - num_lifted_inputs:
        raise AssertionError(
            f"expected {num_placeholders - num_lifted_inputs} shapes, got {len(flat_dynamic_shapes)}"
        )

    free_symbols = set()
    range_violations = []
    for input_index, node in enumerate(gm.graph.nodes):
        meta_val = node.meta.get("val")

        if (
            input_index < num_lifted_inputs
            or node.op != "placeholder"
            or meta_val is None
        ):
            continue

        elif _is_constant_argument(meta_val) or isinstance(meta_val, CustomObjArgument):
            continue

        shape_spec = flat_dynamic_shapes[input_index - num_lifted_inputs]
        keypath = flat_paths[input_index - num_lifted_inputs]
        flat_arg = flat_args[input_index - num_lifted_inputs]

        if isinstance(meta_val, int) or (
            isinstance(meta_val, torch.SymInt) and meta_val.node.expr.is_number
        ):
            pass

        elif isinstance(meta_val, torch.SymInt):
            if shape_spec is not None and isinstance(shape_spec, _DimHint):
                hint = flat_arg
                range_constraints[meta_val.node.expr] &= shape_env.bound_sympy(
                    meta_val.node._expr
                )
                violation = _constrain_user_specified_dimhint_range(
                    meta_val,
                    hint,
                    shape_spec,
                    range_constraints,
                    shape_env,
                    keypath,
                    None,
                )
                if violation:
                    range_violations.append(violation)
            else:
                raise RuntimeError("nyi")
            free_symbols.update(meta_val.node.expr.free_symbols)

        elif isinstance(meta_val, torch.Tensor):
            for i, d in enumerate(node.meta["val"].shape):
                dim = None
                if isinstance(shape_spec, (list, tuple)):
                    dim = shape_spec[i]
                elif isinstance(shape_spec, dict):
                    dim = shape_spec.get(i)
                if not is_int(d):
                    # Compute the range constraint for the symbolic expression corresponding
                    # to this shape dimension and store it.
                    if dim is None or isinstance(dim, _DimHint):
                        range_constraints[d.node.expr] &= shape_env.bound_sympy(
                            d.node.expr
                        )
                    else:
                        range_constraints[d.node.expr] &= ValueRanges(
                            lower=dim.min, upper=dim.max
                        )

                    free_symbols.update(d.node.expr.free_symbols)

                # check user-specified min/max range for DimHints;
                # we might want to do this even if model tracing inferred a static dimension.
                if isinstance(dim, _DimHint):
                    hint = flat_arg.shape[i]
                    violation = _constrain_user_specified_dimhint_range(
                        d, hint, dim, range_constraints, shape_env, keypath, i
                    )
                    if violation:
                        range_violations.append(violation)
        else:
            raise RuntimeError(f"Unfamiliar meta val: {meta_val}")

    if range_violations:
        prefix = "Found the following conflicts between user-specified ranges and inferred ranges from model tracing:\n"
        raise ValueError(prefix + "\n".join(range_violations))

    for symbol in free_symbols:
        if symbol not in range_constraints:
            # Placeholders can have symbolic shapes that are derived expressions.
            # The above code will record direct range constraints for them
            # so that we can do runtime assertions. In addition, for serde checks
            # we want to record range constraints for their root symbols.
            range_constraints[symbol] = shape_env.var_to_range[symbol]

    return dict(range_constraints)