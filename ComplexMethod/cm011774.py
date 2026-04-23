def extract_normalized_read_writes(
    node: Union["FusedSchedulerNode", "SchedulerNode"],
) -> FusedNormalizedReadsWrites | None:
    """Extracts index variables, reduce variables, read/write expressions, and variable ranges from a fused node."""
    reads: dict[sympy.Expr, OrderedSet[str]] = defaultdict(OrderedSet)
    writes: dict[sympy.Expr, OrderedSet[str]] = defaultdict(OrderedSet)

    all_output_names = node.get_buffer_names()
    op_names = node.get_operation_names()
    outputs: OrderedSet[str] = OrderedSet()
    removed_buffers: OrderedSet[str] = OrderedSet()
    for buf_name in all_output_names:
        if V.graph.scheduler.can_buffer_be_removed_through_fusion(buf_name, op_names):
            removed_buffers.add(buf_name)
        else:
            outputs.add(buf_name)

    inputs = OrderedSet(
        dep.name for dep in node.read_writes.reads if dep.name not in removed_buffers
    )

    pointwise_numel: sympy.Expr = node.group[1][0]
    red_numel: sympy.Expr = node.group[1][1]

    pw_splits, red_splits = NodeSplitGetter(node).get_node_splits()

    # lets use different prefix (`n`) to distinguish
    (norm_pw_vars, norm_red_vars), ranges = index_vars_no_squeeze(
        pw_splits, red_splits, prefix="n"
    )

    for n in list(node.get_nodes()):
        if not isinstance(n, torch._inductor.scheduler.SchedulerNode):
            continue

        body = n._body

        n_reads: dict[sympy.Expr, OrderedSet[str]] = defaultdict(OrderedSet)
        n_writes: dict[sympy.Expr, OrderedSet[str]] = defaultdict(OrderedSet)

        # TODO - will the names for all the inputs/outputs accurately
        # reflect mutation, or do I need to remap with mutation_real_name
        for inp in inputs:
            for expr in body.get_all_read_expr(inp):
                n_reads[expr].add(inp)

        for out in outputs:
            for expr in body.get_all_write_expr(out):
                n_writes[expr].add(out)

        if not n_reads and not n_writes:
            continue

        (iter_vars, n_pw_splits), (red_vars, n_red_splits) = get_pw_red_splits(
            n, pointwise_numel, red_numel
        )

        groups = pw_splits + red_splits
        lengths = (n_pw_splits, (n_red_splits))
        lengths = (
            torch._inductor.codegen.simd.SIMDKernel.prepare_split_iteration_lengths(
                groups, lengths, red_numel
            )
        )
        try:
            new_ranges, return_getters_groups = (
                torch._inductor.codegen.simd.SIMDKernel._split_iteration_ranges(
                    groups, lengths
                )
            )
        except torch._inductor.codegen.simd.CantSplit:
            # occasionally with dynamic shapes, we will be unable to prove
            # divisibility
            assert pointwise_numel.free_symbols or red_numel.free_symbols
            return None

        var_map = apply_var_mapping(
            iter_vars,
            red_vars,
            norm_pw_vars,
            norm_red_vars,
            new_ranges,
            return_getters_groups,
        )

        # We create Identity sympy.Functions to prevent expansion to int64,
        # unwrap for tiling analysis.
        def remove_identity(expr: sympy.Expr) -> sympy.Expr:
            return expr.replace(Identity, lambda x: x)

        n_reads_new = {
            sympy_subs(remove_identity(read), var_map): v for read, v in n_reads.items()
        }
        n_writes_new = {
            sympy_subs(remove_identity(write), var_map): v
            for write, v in n_writes.items()
        }

        for expr, buf_names in n_reads_new.items():
            reads[expr] |= buf_names

        for expr, buf_names in n_writes_new.items():
            writes[expr] |= buf_names

    reads = {
        V.graph.sizevars.simplify_with_ranges(r, ranges): v for r, v in reads.items()
    }
    writes = {
        V.graph.sizevars.simplify_with_ranges(w, ranges): v for w, v in writes.items()
    }

    fused_out = FusedNormalizedReadsWrites(
        norm_pw_vars,  # type: ignore[arg-type]
        norm_red_vars,  # type: ignore[arg-type]
        reads,
        writes,
        ranges,
    )
    loop_tiling_log.info("Normalized Fused reads: %s", fused_out)
    return fused_out