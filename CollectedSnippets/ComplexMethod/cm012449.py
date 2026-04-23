def try_loop_split(self, nodes: list[SchedulerNode]):
        """
        Apply loop split optimization.
        When one of the indexing_exprs contains a division, we eliminate the division by splitting the loop
        to avoid non-contiguous loads, subject to the following conditions:
            1. No reduction and no mudular index for all nodes.
            2. The indexing_exprs of all nodes contain only one (or more, but all the same) division,
               where the divisor is an integer and not too small (the divisor > 8), the dividend is
               one of the iter_vars, and this var, i.e. the dimension that needs to be split, is
               contiguous in all other indexing_exprs.

        For example, if the node's var_ranges: {z0: 2, z1: 9216, z2: 960} and indexing_exprs:
        {'index0': 8847360*z0 + 960*z1 + z2, 'index1': 32*z0 + (z2//30), 'index2': z2},
        we will split z2 -> 30*z2 + z3, then the node's var_ranges will be changed to
        {z0: 2, z1: 9216, z2: 32, z3: 30} and indexing_exprs will be changed to
        {'index0': 8847360*z0 + 960*z1 + 30*z2 + z3, 'index1': 32*z0 + z2, 'index2': 30*z2 + z3}.
        """

        # No reduction and no mudular
        if any(
            len(node.group[1][1]) != 0
            or any(
                expr.has(ModularIndexing) for expr in node._body.indexing_exprs.values()
            )
            for node in nodes
        ):
            return nodes

        split_var = None
        split_number = None
        num_div = 0
        div_expr_ = None
        match_div = False
        matched_node = None
        matched_index_size = None

        # Collect node info for later compatibility check
        node_bodies: list[tuple[Any, Any]] = []

        for node in nodes:
            assert isinstance(node.node, ir.ComputedBuffer)
            sizes_body = node.node.get_default_sizes_body()
            node_bodies.append((node, sizes_body))
            (index_size, _), original_body, _ = sizes_body
            for name, expr in original_body.indexing_exprs.items():
                if not isinstance(expr, sympy.Expr):
                    continue
                for div_expr in expr.find(FloorDiv):
                    if (
                        any(div_expr.has(var) for var in original_body.iter_vars)
                        and div_expr != div_expr_
                    ):
                        div_expr_ = div_expr
                        num_div += 1
                    if num_div > 1:
                        return nodes
                    if (
                        isinstance(div_expr.args[1], sympy.core.numbers.Integer)
                        and div_expr.args[0] in original_body.iter_vars
                        and name is not None
                        and all(
                            stride_at_vec_range(expr_, div_expr.args[0]) in (0, 1)
                            for name_, expr_ in original_body.indexing_exprs.items()
                            if name_ != name
                        )
                        and div_expr.args[1] > 8
                    ):
                        split_var = div_expr.args[0]
                        split_number = div_expr.args[1]
                        match_div = True
                        matched_node = node
                        matched_index_size = index_size

        # Only one node contains a division, and the split dimension is contiguous in all other indexing_exprs.
        if not match_div:
            return nodes

        # Check if all nodes have split_var in their iter_vars and have compatible sizes
        # (same number of index dimensions). If not, bail out to avoid incompatible
        # var_ranges after loop split which would cause assertion failures in
        # simplify_and_reorder or codegen_functions.
        assert matched_index_size is not None
        matched_num_dims = len(matched_index_size)

        for node, ((index_size, _), original_body, _) in node_bodies:
            if split_var not in original_body.iter_vars:
                return nodes
            if len(index_size) != matched_num_dims:
                return nodes

        extra_indexing_constraints = None

        def loop_split(sizes, body, vars):
            index_size, reduce_size = sizes
            index_vars, reduce_vars = vars
            split_idx = index_vars.index(split_var)
            new_index_size = index_size.copy()
            new_index_size[split_idx] = index_size[split_idx] // split_number
            new_index_size.insert(split_idx + 1, split_number)
            (new_index_vars, _), var_ranges = dependencies.index_vars_no_squeeze(
                new_index_size, reduce_size, prefix="y"
            )
            iter_vars = new_index_vars.copy()
            divisor_var = iter_vars.pop(split_idx + 1)
            iter_vars[split_idx] = split_number * iter_vars[split_idx] + divisor_var
            body = ir.LoopBody(
                body, [iter_vars, reduce_vars], var_ranges, new_index_vars, reduce_vars
            )
            nonlocal extra_indexing_constraints
            if not extra_indexing_constraints:
                extra_indexing_constraints = (
                    body.var_ranges,
                    list(body.indexing_exprs.values()),
                )
            return (
                (new_index_size, reduce_size),
                body,
                (new_index_vars, reduce_vars),
            )

        # Here decide the final loop order
        for node in nodes:
            if node == matched_node:
                node.recompute_size_and_body(recompute_sizes_body_func=loop_split)
        for node in nodes:
            if node != matched_node:
                node.recompute_size_and_body(
                    extra_indexing_constraints=extra_indexing_constraints,
                    recompute_sizes_body_func=loop_split,
                )

        return nodes