def process_node_vars(
            vars_to_use: tuple[sympy.Expr, ...] = (),
            use_split_var: bool = False,
            is_pointwise: bool = False,
        ) -> tuple[list[int], list[int]]:
            """
            Generate a tiling, and a tiling score, given vars to use as splits.
            """

            ranges = pw_ranges if is_pointwise else red_ranges
            target_numel = pointwise_numel if is_pointwise else reduction_numel
            # Some kernels have no reduction ranges, and a reduction numel of 1
            if not ranges:
                if target_numel:
                    return ([target_numel], [])
                else:
                    return ([], [])

            key = (repr(vars_to_use), use_split_var, is_pointwise)
            if out := scored_sub_split.get(key):
                return out

            splitting_vars = all_iter_vars if is_pointwise else all_red_vars

            splits = []
            split_scores = []
            prod = 1
            prev_var_coalesced_score = 0

            # iterate from non-dense to dense
            for v, v_range in zip(splitting_vars, ranges):
                if v not in vars_to_use:
                    prod *= v_range
                    prev_var_coalesced_score = coalesce_analysis.coalesced_by_var.get(
                        v, 0
                    )
                    continue

                if use_split_var and v == tiling_var:
                    var_tiling = coalesce_analysis.suggested_split
                    assert var_tiling is not None

                    tile = var_tiling.tiling_factor
                    remainder = FloorDiv(v_range, var_tiling.tiling_factor)

                    splits.append(prod * remainder)
                    split_scores.append(var_tiling.score)

                    splits.append(tile)
                    split_scores.append(coalesce_analysis.coalesced_by_var.get(v, 0))

                    prod = 1
                    prev_var_coalesced_score = 0

                    continue

                prod *= v_range
                splits.append(prod)
                split_scores.append(coalesce_analysis.coalesced_by_var.get(v, 0))
                prod = 1

            if prod != 1 or (is_pointwise and len(splits) == 0):
                splits.append(prod)
                split_scores.append(prev_var_coalesced_score)

            # penalize splits that leave small blocks
            # where we can't fully utilize full memory transaction
            # TODO: incorporate exact bitwidth, and read/write
            # coalesced write is 2x more important
            for i in range(len(splits)):
                s = V.graph.sizevars.optimization_hint(splits[i], fallback=32)
                s = min(s, 8)
                split_scores[i] = int(split_scores[i] * s / 8)

            scored_sub_split[key] = (splits, split_scores)
            return (splits, split_scores)