def check_outer_fusion_loop_level_attr(
        self, cpp_kernel_proxy_list, outer_loop_fusion_depth
    ):
        # This function ensures that the same tiling split is applied at each loop level within the outer loop fusion depth.
        # In the fusion stage, we only examine nodes with same vars and reduce.
        # However, for nodes with same vars and reduce, the loops may still have different tile splits.
        # For example (test_expr_vec_non_contiguous in test_cpu_repro.py):
        #   * buf0 tiling along the 2nd loop level, buf1 tiling along the 3rd loop level.
        # If the check failed, we should fall back to standard loop codegen.
        def _inner(
            left_loop_nest: LoopNest,
            right_loop_nest: LoopNest,
            loop_fusion_depth: int,
            current_checking_depth: int,
        ) -> bool:
            assert left_loop_nest.loops
            assert right_loop_nest.loops
            left_loop_level = left_loop_nest.loops[current_checking_depth]
            right_loop_level = right_loop_nest.loops[current_checking_depth]
            # Check if same loop level attr
            outer_loops_attr_compare_list = [
                "var",
                "size",
                "offset",
                "steps",
            ]
            if not (
                all(
                    getattr(left_loop_level, attr_compare)
                    == getattr(right_loop_level, attr_compare)
                    for attr_compare in outer_loops_attr_compare_list
                )
            ):
                return False

            assert loop_fusion_depth >= 1
            if (loop_fusion_depth := loop_fusion_depth - 1) > 0:
                # Check next loop level attr
                current_checking_depth = current_checking_depth + 1
                assert current_checking_depth < len(left_loop_nest.loops)
                assert current_checking_depth < len(right_loop_nest.loops)
                if not _inner(
                    left_loop_nest,
                    right_loop_nest,
                    loop_fusion_depth,
                    current_checking_depth,
                ):
                    return False

            return True

        for idx in range(len(cpp_kernel_proxy_list) - 1):
            left_loop_nest = cpp_kernel_proxy_list[idx].loop_nest
            right_loop_nest = cpp_kernel_proxy_list[idx + 1].loop_nest
            if not _inner(
                left_loop_nest,
                right_loop_nest,
                outer_loop_fusion_depth,
                0,
            ):
                return False

        for cpp_kernel_proxy in cpp_kernel_proxy_list:
            outer_ranges = functools.reduce(
                operator.mul,
                cpp_kernel_proxy.ranges[:outer_loop_fusion_depth],
            )
            # When the range of the first inner loop is much larger than the range of
            # all outer loops, do not fuse outer loop and fallback to standard loop codegen,
            # so that the inner loops with larger range have a chance to be parallelized.
            # We set a conservative threshold here:
            # First inner loop range / all outer loops range > 300.
            if (
                len(cpp_kernel_proxy.ranges) > outer_loop_fusion_depth
                and isinstance(outer_ranges, sympy.Integer)
                and isinstance(
                    cpp_kernel_proxy.ranges[outer_loop_fusion_depth],
                    sympy.Integer,
                )
                and outer_ranges * 300
                < cpp_kernel_proxy.ranges[outer_loop_fusion_depth]
            ):
                return False

        return True