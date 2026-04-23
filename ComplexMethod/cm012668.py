def get_tiling_and_scores(
        cls,
        node_schedule,
        numel,
        reduction_numel=sympy.S.One,
        coalesce_analysis: CoalesceVarAnalysis | None = None,
    ) -> tuple[dict[str, sympy.Expr], dict[str, sympy.Expr] | None]:
        """
        Heuristics to decide how to tile kernels.
        Currently, we tile based on stride-1 dimensions.

        Returns:
            `(tile1, tile2, reduction_numel)` s.t. `tile1 * tile2 == numel`

        """
        # If this is a reduction, only tile reduction dims.
        is_pointwise = reduction_numel == 1

        # Tiled reductions are gated by a config flag.
        default_tiling = cls.create_tiling([numel], [reduction_numel])

        # Force tiling compatible with matmul dimensions
        # when natively generating matmul without template calls.
        for node in EnableReduction.filter(node_schedule):
            if isinstance(node.node, ir.ComputedBuffer):
                if (
                    node.node.get_reduction_type() == "dot"
                    and config.triton.native_matmul
                ):
                    # A[M,K] @ B[K,N]
                    # force tiling to be {'y':M, 'x':N, 'r0_':K}
                    node_ranges = node.get_ranges()
                    range_y_x = node_ranges[0]  # (M,N)
                    range_r = node_ranges[1]  # (K)
                    tiling = cls.create_tiling(range_y_x, range_r)
                    return tiling, None

        # # TODO: enable by default
        if (
            torch._inductor.config.triton.coalesce_tiling_analysis
            and coalesce_analysis
            and not config.triton.prefer_nd_tiling
        ):
            return cls.compute_tiling_strategy(
                node_schedule, numel, reduction_numel, coalesce_analysis
            )

        if (not is_pointwise and not config.triton.tile_reductions) or get_max_tiles(
            default=2
        ) <= 1:
            # Emit a perf hint in case we miss an opportunity to tile a reduction.
            if perf_hint_log.level <= logging.WARNING:
                for node in EnableReduction.filter(node_schedule):
                    if (
                        not config.triton.tile_reductions
                        and len(cls.candidate_tilings(node, numel, reduction_numel)) > 0
                    ):
                        perf_hint_log.info(
                            textwrap.dedent(
                                """
                                Reduction over non-contiguous dims.
                                Consider setting config.triton.tile_reductions to True.
                                """
                            )
                        )
                        break

            return default_tiling, None

        seen_names: OrderedSet[str] = OrderedSet()
        candidate_tiles: Counter[CandidateTiling] = collections.Counter()
        for node in EnableReduction.filter(node_schedule):
            for candidate_tiling in cls.candidate_tilings(node, numel, reduction_numel):
                if candidate_tiling.name in seen_names:
                    continue
                elif candidate_tiling.name is not None:
                    seen_names.add(candidate_tiling.name)
                candidate_tiles[candidate_tiling] += candidate_tiling.score

        ranked_tilings: list[dict[str, sympy.Expr]] = [
            candidate_tiling.tiling
            for candidate_tiling, score in candidate_tiles.most_common()
        ]

        if get_max_tiles(default=2) >= 3 and is_pointwise:
            # Consider adding a third dimension of tiling, but only
            # when a1 is a multiple of b1; otherwise, you have a lot
            # of stragglers which is annoying to generate code for.
            #
            # NB: More than three max tiles is not enabled by default.

            def convert_tiling_to_3d(
                tiling0: dict[str, sympy.Expr], tiling1: dict[str, sympy.Expr]
            ) -> dict[str, sympy.Expr] | None:
                a0, a1 = tiling0["x"], tiling0.get("y", 1)
                b0, b1 = tiling1["x"], tiling1.get("y", 1)

                # TODO: These tiling decisions (equality, ordering, divisibility)
                # are structural — they determine the kernel's iteration space
                # decomposition — but are NOT guarded here. If the relationship
                # between a1 and b1 changes across dynamic shape inputs, the
                # compiled kernel could be wrong. Seems scary, unless there is a reason
                # this is safe in that case probably we need better comment here !
                hint = V.graph.sizevars.guarding_hint_or_throw
                if hint(a1 - b1) == 0:
                    return None
                if hint(a1 - b1) < 0:
                    # swap so a0 is bigger
                    (a0, a1), (b0, b1) = (b0, b1), (a0, a1)

                assert hint(a1 - b1) > 0
                if not V.graph.sizevars.statically_known_multiple_of(a1, b1):
                    return None

                new_tiling = {
                    "z": a0,
                    "y": FloorDiv(a1, b1),
                    "x": b1,
                    "r0_": tiling0["r0_"],
                }

                return new_tiling

            for i in range(1, len(ranked_tilings)):
                new_3d_tiling = convert_tiling_to_3d(
                    ranked_tilings[0], ranked_tilings[i]
                )
                if new_3d_tiling is not None:
                    ranked_tilings = [new_3d_tiling] + ranked_tilings
                    break  # only 1 choice for now

        if len(ranked_tilings) > 1:
            perf_hint_log.info("possibly bad tiling: %s", ranked_tilings)

        # Optionally, prefer tiling into as many dimensions as possible.
        # pyrefly: ignore [unbound-name]
        if config.triton.prefer_nd_tiling:
            ranked_tilings = (
                cls.get_nd_tilings(node_schedule, numel, reduction_numel)
                + ranked_tilings
            )

        if tiling := cls.get_first_compatible_tiling(
            node_schedule, numel, reduction_numel, ranked_tilings
        ):
            return tiling, None

        return default_tiling, None