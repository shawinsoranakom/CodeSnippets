def _cat_inputs_recombine_reduction(inputs: list[TensorBox], dim: int) -> str | None:
    """If all cat inputs share a common upstream reduction buffer whose
    only consumers feed into this cat, return its name so it can be
    excluded from the can_fuse_reduction check.

    Checks common reads for an IR reduction whose numel matches the cat
    output, then verifies via FX origins that all of the reduction's
    consumers feed into the cat inputs."""
    if len(inputs) < 2:
        return None

    common_reads = inputs[0].get_read_names()
    for inp in inputs[1:]:
        common_reads = common_reads & inp.get_read_names()
    if not common_reads:
        return None

    # Find a common read that is an IR reduction buffer whose input
    # numel matches the cat output numel.
    cat_out_numel = convert_symint_to_expr(V.graph.current_node.meta["val"].numel())
    reduction_name = None
    reduction_buf = None
    for name in common_reads:
        buf = V.graph.try_get_buffer(name)
        if (
            buf is not None
            and isinstance(buf, ir.ComputedBuffer)
            and isinstance(buf.data, ir.Reduction)
        ):
            reduction_numel = sympy_product(buf.data.get_size()) * sympy_product(
                buf.data.get_reduction_size()
            )
            if V.graph.sizevars.statically_known_equals(cat_out_numel, reduction_numel):
                reduction_name = name
                reduction_buf = buf
                break

    if reduction_name is None:
        return None

    # Verify the reduction doesn't have consumers outside this cat's
    # computation. Each IR node tracks which FX nodes produced it
    # (origins). Collect the FX origins of all cat inputs, then check
    # that every FX user of the reduction's origins feeds into one of
    # the cat inputs.
    #
    # We also tried checking IR-level users via V.graph.name_to_users,
    # but at lowering time the cat inputs are unrealized TensorBox
    # wrappers (not named buffers), so name_to_users entries can't be
    # correlated back to the cat's input chain.
    #
    # TODO: origins is a set of FX nodes attached to IR nodes during
    # lowering — using it for correctness is fragile. A proper
    # buffer→FX node mapping would be better.
    origins = getattr(reduction_buf, "origins", None)
    if not origins:
        return None

    cat_input_origins: OrderedSet[torch.fx.Node] = OrderedSet()
    for inp in inputs:
        inp_origins = getattr(inp, "origins", None)
        if inp_origins:
            cat_input_origins.update(inp_origins)

    # Check that the reduction FX node's users all feed into the cat.
    # origins may include non-reduction nodes (e.g. pow that feeds into
    # mean), so filter to only reduction ops via torch.Tag.reduction.
    for origin in origins:
        if (
            origin.op == "call_function"
            and isinstance(origin.target, torch._ops.OpOverload)
            and torch.Tag.reduction in origin.target.tags
            and not all(u in cat_input_origins for u in origin.users)
        ):
            return None

    return reduction_name