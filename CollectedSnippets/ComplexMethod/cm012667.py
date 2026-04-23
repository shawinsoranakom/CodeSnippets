def compute_tiling_strategy(
        cls,
        node_schedule: list[NodeScheduleEntry],
        pointwise_numel: sympy.Expr,
        reduction_numel: sympy.Expr,
        coalesce_analysis: CoalesceVarAnalysis,
    ) -> tuple[dict[str, sympy.Expr], dict[str, sympy.Expr] | None]:
        """
        Generates a tiling, and a score of each tile according to each tile's coalesced memory accesses.
        """
        tiling_var: sympy.Expr | None = (
            None
            if not coalesce_analysis.suggested_split
            else coalesce_analysis.suggested_split.var
        )

        all_iter_vars = coalesce_analysis.norm_read_writes.index_vars
        all_red_vars = coalesce_analysis.norm_read_writes.reduce_vars
        ranges = coalesce_analysis.norm_read_writes.var_ranges

        pw_ranges = [ranges[v] for v in all_iter_vars]
        red_ranges = [ranges[v] for v in all_red_vars]

        # Sometimes dynamic shapes is unable to prove equality without hint
        get_hint = V.graph.sizevars.optimization_hint
        torch._check(
            get_hint(sympy_product(pw_ranges)) == get_hint(pointwise_numel),
            lambda: f"{pw_ranges}, {pointwise_numel}, {node_schedule}",
        )

        torch._check(
            get_hint(sympy_product(red_ranges)) == get_hint(reduction_numel),
            lambda: f"{red_ranges}, {reduction_numel}, {node_schedule}",
        )

        # score of a pointwise or reduction split
        scored_sub_split: dict[Any, tuple[list[int], list[int]]] = {}

        score_split: list[
            tuple[tuple[list[int], list[int]], tuple[list[int], list[int]]]
        ] = []

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

        # add the default tiling
        score_split.append(
            (
                process_node_vars(is_pointwise=True),
                process_node_vars(is_pointwise=False),
            )
        )

        if tiling_var:
            score_split.append(
                (
                    process_node_vars(
                        (tiling_var,), use_split_var=True, is_pointwise=True
                    ),
                    process_node_vars(is_pointwise=False),
                )
            )

        # TODO, add tests, reduction splits if config.triton.tile_reductions
        # TODO: we should ignore tiny increases in score for extra splits
        overlapping_iter_vars = (
            all_iter_vars & coalesce_analysis.coalesced_by_var.keys()
        )
        for v in overlapping_iter_vars:
            score_split.append(
                (
                    process_node_vars((v,), is_pointwise=True),
                    process_node_vars(is_pointwise=False),
                )
            )

        if get_max_tiles(default=3) == 3 and reduction_numel == 1:
            for vars_to_use in itertools.combinations(overlapping_iter_vars, 2):
                score_split.append(
                    (
                        process_node_vars(vars_to_use, is_pointwise=True),
                        process_node_vars(is_pointwise=False),
                    )
                )

        tilings: list[tuple[CandidateTiling, immutable_dict[str, sympy.Expr]]] = []
        for (pw_split, pw_score), (red_split, red_score) in score_split:
            candidate = CandidateTiling(
                cls.create_tiling(pw_split, red_split),
                score=sum(pw_score) + sum(red_score),
            )
            tiling_score = cls.create_tiling(pw_score, red_score)
            tilings.append((candidate, tiling_score))

        default_tiling = cls.create_tiling([pointwise_numel], [reduction_numel])

        # add a slight penalty for longer tilings that dont increase score much,
        # and are poor sizes
        bad_size_additional_tiling_penalty = 1.025
        good_size_tiling_penalty = 1.005

        total_uncoalesced = sum(coalesce_analysis.uncoalesced_addrs.values())

        def score_mod(t):
            score_factor = 1.0
            for tile_size in t[0].tiling.values():
                if not CandidateTiling.is_good_size(tile_size):
                    score_factor = score_factor / bad_size_additional_tiling_penalty
                else:
                    score_factor = score_factor / good_size_tiling_penalty

            # Add uncoalesced memory score to prevent small coalesced benefits
            # from dominating large amounts of uncoalesced memory
            uncoalesced_penalty = total_uncoalesced * 0.05

            return -(t[0].score + uncoalesced_penalty) * score_factor

        # apply penalty for longer tilings that dont increase score much
        for cand, tiling_score in sorted(tilings, key=score_mod):
            if (
                cls.tiling_is_compatible(
                    node_schedule, pointwise_numel, reduction_numel, cand.tiling
                )
                or cand.tiling == default_tiling
            ):
                # we always include default reduction numel == 1, dont include
                tiling_len = len(cand.tiling) - (1 if reduction_numel == 1 else 0)
                if tiling_len > get_max_tiles(default=3):
                    perf_hint_log.info(
                        "Found optimal tiling with %s tiles but torch._inductor.config.triton.max_tiles "
                        "set to %s. Consider increasing",
                        tiling_len,
                        torch._inductor.config.triton.max_tiles,
                    )
                    continue

                return cand.tiling, tiling_score

            # surprisingly, the default tiling is not always read as compatible by `tiling_is_compatible`
            # TODO - look into, occurs with dynamic shapes often
            if cand.tiling == default_tiling:
                return cand.tiling, tiling_score

        return default_tiling, None