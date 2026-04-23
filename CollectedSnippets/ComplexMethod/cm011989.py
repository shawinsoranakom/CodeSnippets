def simplify_and_reorder(
        self,
        extra_indexing_constraints: tuple[dict[Any, Any], list[Any]] | None = None,
        recompute_sizes_body_func: Callable[..., Any] | None = None,
    ) -> tuple[tuple[list[Expr], list[Expr]], LoopBody | None]:
        """
        This is a main place where we do loop transformations in a
        backend-agnostic way.

        Here we:
            1) Remove any 1 dimensions
            2) Fuse contiguous dimensions together
            3) Reorder dimensions based on stride orders

        Optional argument extra_indexing_constraints can be used to append additional
        indexing expressions to existing ones derived from buffer's body. This can be useful
        to fuse scheduler nodes with compatible ranges, e.g. (s0*s1*...,) and (s0, s1, s2, ...)
        on CPU by preventing indexing simplifications and obtaining index/reduce ranges for
        the scheduler node compatible with other nodes.
        Optional argument recompute_sizes_body_func can be used to recompute sizes and body
        on the default body. This can be useful to append additional loop transformations.
        """
        (
            (index_size, reduce_size),
            body,
            (index_vars, reduce_vars),
        ) = self.get_default_sizes_body()

        if recompute_sizes_body_func:
            (
                (index_size, reduce_size),
                body,
                (index_vars, reduce_vars),
            ) = recompute_sizes_body_func(
                (index_size, reduce_size), body, (index_vars, reduce_vars)
            )

        index_formulas = [*body.indexing_exprs.values()]
        if extra_indexing_constraints is not None:
            assert (
                isinstance(extra_indexing_constraints, tuple)
                and len(extra_indexing_constraints) == 2
            )
            extra_indexing_ranges, extra_indexing_expr = extra_indexing_constraints
            assert isinstance(extra_indexing_ranges, dict), type(extra_indexing_ranges)
            assert isinstance(extra_indexing_expr, list), type(extra_indexing_expr)
            assert all(isinstance(f, Expr) for f in extra_indexing_expr)

            expected_var_ranges = body.var_ranges
            assert expected_var_ranges == extra_indexing_ranges, (
                expected_var_ranges,
                extra_indexing_ranges,
            )
            # remove already existing expressions
            extra_indexing_expr = [
                e for e in extra_indexing_expr if e not in index_formulas
            ]
            index_formulas += extra_indexing_expr

        memory_addrs = [*body.get_write_exprs()]
        if not V.graph.has_feature(self, BackendFeature.PREFER_STORE_LOOP_ORDER):
            memory_addrs.extend(body.get_read_exprs())

        def simplify_and_reorder(
            x_vars: Sequence[sympy.Symbol],
            support_vars: Sequence[sympy.Symbol],
            sizes: Sequence[int],
            simplify_loops: bool,
        ) -> tuple[
            list[int],
            Callable[[Sequence[int]], Sequence[int]],
            Callable[[Sequence[int]], Sequence[int]],
        ]:
            newsizes, reindex0, reindex1 = self._apply_loop_reordering(
                x_vars, support_vars, sizes, memory_addrs
            )

            # When using native matmul, the codegen assumes the following loop order,
            # regardless of the stride of A and B:
            #
            #   for z -> y -> x -> r:  C[z, y, x] += A[z, y, r] * B[z, r, x]
            # or
            #   for z -> x -> y -> r:  C[z, y, x] += A[z, y, r] * B[z, r, x]
            #
            # The critical point is the position of the "z" (batch) axis in bmm.
            # It is fine to swap the y and x axes (e.g., (z, y, x, r) or (z, x, y, r)),
            # but reordering the z axis (e.g., (y, x, z, r)) breaks codegen.
            #
            # Therefore, if loop reordering changes the "z" location in bmm,
            # it should be reverted to the default.
            # This may not always produce the optimal loop order when strides
            # do not align with the default assumption.
            #
            # TODO: Consider extending tl.dot codegen to support arbitrary loop orders.
            if self.get_reduction_type() == "dot" and len(sizes) == 3:
                order = list(range(len(sizes)))  # default order

                # if z axis is not the outermost, use the default reorder.
                if reindex0(order)[0] != 0:
                    newsizes = [sizes[i] for i in order]
                    reindex0 = same_reorder(order)
                    reindex1 = inverse_reorder(order)

            # for NHWC: reindex0([0,1,2,3]) = [0,2,3,1], reindex1([0,1,2,3]) = [0,3,2,1]
            x_vars = reindex0(x_vars)

            if simplify_loops:
                newsizes, reindex2, _prune = V.graph.sizevars._simplify_loops(
                    x_vars,
                    newsizes,
                    index_prevent_reordering(index_formulas, x_vars, newsizes),
                )
                reindex = fuse_reindexing(reindex1, reindex2)
            else:
                reindex = reindex1
            return newsizes, reindex, reindex1

        support_vars = index_vars + reduce_vars
        should_merge_loops = (
            not is_gpu(get_device_type(self)) or not config.loop_ordering_after_fusion
        )
        iter_ranges, iter_reindex, _ = simplify_and_reorder(
            index_vars,
            support_vars,
            index_size,
            should_merge_loops,
        )

        # Like iteration dimensions, we may also want to delay merging reduction dimensions.
        # E.g., if we reduce a tensor [M, N, K] for its M and N dimensions followed by a pointwise
        # kernel, merging M and N dimension too early makes it hard to decide what loop order
        # we should pick for the piontwise kernel so that it is fusible with the reduction.
        reduce_ranges, reduce_reindex, _ = simplify_and_reorder(
            reduce_vars, support_vars, reduce_size, should_merge_loops
        )

        # retrace the loop body with simplification and reordering applied
        (iter_vars, reduce_vars), var_ranges = dependencies.index_vars_no_squeeze(
            iter_ranges,
            reduce_ranges,
            prefix="p",
        )
        body = LoopBody(
            body,
            [iter_reindex(iter_vars), reduce_reindex(reduce_vars)],
            var_ranges,
            iter_vars,
            reduce_vars,
        )
        return (iter_ranges, reduce_ranges), body