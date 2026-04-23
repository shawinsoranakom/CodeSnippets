def select_tiling(
        self,
        fn_list,
        var_sizes_list,
    ) -> tuple[list[int], list[int]]:
        # TODO(jgong5): support alternative tiling factors and data types
        loop_bodies = _get_loop_body(fn_list)
        all_dtypes = _get_dtype_from_loopbodies(loop_bodies)
        assert all_dtypes
        if any(dtype not in VECTORIZABLE_DTYPES for dtype in all_dtypes):
            return [], []
        dtype = torch.float
        _lowp_fp_dtype = get_loop_body_lowp_fp(loop_bodies[0])[0]
        if _lowp_fp_dtype and all(
            (get_loop_body_lowp_fp(loop_body)[0] == _lowp_fp_dtype)
            for loop_body in loop_bodies[1:]
        ):
            dtype = _lowp_fp_dtype

        tiling_factor = cpu_vec_isa.pick_vec_isa().nelements(dtype=dtype)
        tiling_indices = self._select_tiling_indices(
            fn_list, var_sizes_list, tiling_factor
        )

        if tiling_indices:
            group, reduction_group = max(
                var_sizes_list, key=lambda sizes: len(sizes[1])
            )
            call_ranges = tuple(group) + tuple(reduction_group)

            if config.cpp.enable_tiling_heuristics:

                def _try_get_stride(
                    index,
                    itervars,
                    tiling_factor,
                    tiling_indices,
                ):
                    itervar = itervars[tiling_indices[0]]
                    stride = stride_at_vec_range(index, itervar, tiling_factor)
                    return stride if stride.is_number else None

                def _update_negative_op_count(
                    node_name, non_contig_indexing_op_counter
                ):
                    if node_name not in non_contig_indexing_op_counter:
                        non_contig_indexing_op_counter[node_name] = 1
                    else:
                        non_contig_indexing_op_counter[node_name] += 1

                def _is_valid_indices(
                    itervars,
                    tiling_indices,
                ):
                    return (
                        len(tiling_indices) == 1
                        and len(itervars) > 0
                        and (
                            tiling_indices[0]
                            if tiling_indices[0] >= 0
                            else tiling_indices[0] + len(itervars)
                        )
                        < len(itervars)
                    )

                itervars = [
                    sympy_index_symbol_with_prefix(SymT.XBLOCK, n)
                    for n in range(len(call_ranges))
                ]
                reduction_depth = len(group)
                vars, reduction_vars = (
                    itervars[:reduction_depth],
                    itervars[reduction_depth:],
                )
                op_counter: dict[str, int] = {}
                # ops may cause overhead with vectorization, like non-contiguous
                # index_expr, load, store
                non_contig_indexing_op_counter: dict[str, int] = {}
                for _body in loop_bodies:
                    sub_blocks = [_body.root_block] + list(_body.subblocks.values())
                    for sub_block in sub_blocks:
                        for _node in sub_block.graph.nodes:
                            if _node.target in ["index_expr", "load", "store"]:
                                # get the index and replace prefix from z to x
                                arg_idx = 1 if _node.target == "index_expr" else 2
                                index = sub_block.body.indexing_from_args(
                                    (vars, reduction_vars)
                                )[_node.args[arg_idx].args[0]]
                                if _is_valid_indices(itervars, tiling_indices):
                                    stride = _try_get_stride(
                                        index, itervars, tiling_factor, tiling_indices
                                    )
                                    if (
                                        stride is None
                                        if _node.target == "index_expr"
                                        else stride not in [0, 1]
                                    ):
                                        _update_negative_op_count(
                                            _node.target, non_contig_indexing_op_counter
                                        )
                            if isinstance(_node.target, str) and not (
                                _node.target.startswith("masked_subblock")
                                or _node.target
                                in ["ops", "output", "constant", "get_index"]
                            ):
                                if _node.target not in op_counter:
                                    op_counter[_node.target] = 1
                                else:
                                    op_counter[_node.target] += 1

                op_num = sum(op_counter.values())
                non_contig_indexing_op_num = sum(
                    non_contig_indexing_op_counter.values()
                )
                ratio_threshold = 0.12
                quantity_threshold = 35
                if non_contig_indexing_op_num >= quantity_threshold or (
                    op_num > 0
                    and non_contig_indexing_op_num / op_num >= ratio_threshold
                ):
                    # Too many non-contiguous load/store/index_expr which hurts the
                    # vectorization performance. Disable vectorization when exceeding
                    # the thresholds.
                    return [], []

                if (
                    not reduction_group
                    and group
                    and len(tiling_indices) == 1
                    and not has_free_symbols(
                        [
                            group[tiling_indices[0]],
                        ]
                    )
                    and group[tiling_indices[0]] < tiling_factor / 4
                    and op_num < 10
                ):
                    # We found that when the number of elements in the inner loop range is
                    # relatively small(< tiling_factor / 4) and the number of operations is
                    # not large(< 10), vectorization is not efficient.
                    # And found that `#pragma GCC ivdep` has better performance than
                    # `#pragma omp simd simdlen(8)` for these cases.
                    return [], []

            if dtype in DTYPE_LOWP_FP:
                # For lower precision data type, if the call_range is not long enough,
                # use tiling_factor // 2 for better performance
                factor_lowp = cpu_vec_isa.pick_vec_isa().nelements(dtype=dtype)
                for tiling_indice in tiling_indices:
                    if tiling_indice < 0:
                        tiling_indice = tiling_indice + len(call_ranges)
                    if tiling_indice < 0 or tiling_indice >= len(call_ranges):
                        continue
                    if has_free_symbols(call_ranges):
                        call_range = V.graph.sizevars.optimization_hint(
                            call_ranges[tiling_indice], fallback=0
                        )
                        if call_range < factor_lowp:
                            V.graph.sizevars.check_lt(call_range, factor_lowp)  # type: ignore[arg-type]
                            tiling_factor = factor_lowp // 2
                            break
                    elif call_ranges[tiling_indice] < factor_lowp:
                        tiling_factor = factor_lowp // 2
                        break

            if len(tiling_indices) == 1:
                return [tiling_factor], tiling_indices
            if len(tiling_indices) == 2:
                return [tiling_factor, tiling_factor], tiling_indices
        return [], []