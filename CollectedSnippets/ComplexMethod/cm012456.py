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