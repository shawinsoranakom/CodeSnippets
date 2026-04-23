def produce_guards_and_solve_constraints(
    fake_mode: FakeTensorMode,
    gm: torch.fx.GraphModule,
    dynamic_shapes: dict[str, Any] | tuple[Any] | list[Any] | None,
    equalities_inputs: EqualityConstraint,
    original_signature: inspect.Signature,
):
    """
    Given a fake mode, sources pairs corresponding to equal dynamic shape dimensions,
    and a graph module, produce guards on the fake mode's shape env (raising constraint
    violations if any), solve (to suggest simplifications or fixes).
    Dynamo already performs this, so this is for non-strict mode.

    Additional inputs:
        equalities_inputs: the equality constraints to use for guards
        original_signature: the signature of the forward method
    """
    shape_env = fake_mode.shape_env
    if shape_env is None:
        raise AssertionError("fake_mode.shape_env must not be None")
    if shape_env.tracked_fakes is None:
        raise AssertionError("shape_env.tracked_fakes must not be None")

    placeholders = [tf.fake for tf in shape_env.tracked_fakes]
    sources = [tf.source for tf in shape_env.tracked_fakes]
    input_contexts = [tf.symbolic_context for tf in shape_env.tracked_fakes]
    constraint_violation_error = None
    try:
        shape_env.produce_guards(
            placeholders,
            sources,
            input_contexts=input_contexts,
            equalities_inputs=equalities_inputs,
            ignore_static=False,
        )
    except ConstraintViolationError as e:
        constraint_violation_error = e

    shape_env.frozen = True
    dim_constraints = shape_env.dim_constraints
    if dim_constraints is None:
        # Expected when shape_env.produce_guards throws an early constraint violation error.
        # There is nothing to solve for in this case.
        # TODO(avik): Maybe record the constraint violation error instead and replay later?
        if not constraint_violation_error:
            raise AssertionError(
                "expected constraint_violation_error when dim_constraints is None"
            )
        raise constraint_violation_error
    dim_constraints.solve()
    forced_specializations = dim_constraints.forced_specializations()

    msg = dim_constraints.prettify_results(
        original_signature,
        dynamic_shapes,  # type: ignore[arg-type]
        constraint_violation_error,
        forced_specializations,  # type: ignore[arg-type]
    )

    if constraint_violation_error:
        if constraint_violation_error.args:
            constraint_violation_error.args = (
                constraint_violation_error.args[0] + msg,
            )
        else:
            constraint_violation_error.args = (msg,)
    elif forced_specializations:
        constraint_violation_error = ConstraintViolationError(msg)
    if constraint_violation_error:
        raise constraint_violation_error