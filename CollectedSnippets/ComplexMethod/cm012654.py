def _split_iteration_ranges(
        groups: Iterable[sympy.Expr], lengths: Sequence[Sequence[sympy.Expr]]
    ) -> tuple[
        list[list[sympy.Expr]], list[list[Callable[[list[sympy.Expr]], sympy.Expr]]]
    ]:
        # Special case: if a node's sizes are ([], []), there's nothing to split.
        if all(len(length) == 0 for length in lengths):
            return [[] for group in groups], []

        sv = V.graph.sizevars
        new_ranges: list[list[sympy.Expr]] = [[] for _ in groups]
        remaining = [sv.simplify(g) for g in groups]
        var_count = itertools.count()

        def add_range(i: int, expr: sympy.Expr) -> int:
            expr = sv.simplify(expr)
            if not sv.statically_known_multiple_of(remaining[i], expr):
                raise CantSplit(remaining[i], expr)
            # guard on the last item out
            remaining[i] = FloorDiv(remaining[i], expr)
            new_ranges[i].append(expr)
            return next(var_count)

        def make_combined(
            sizes: list[sympy.Expr], idxs: list[int]
        ) -> Callable[[list[sympy.Expr]], sympy.Expr]:
            """
            Builds the nested expression:
              ((...((s1*v[i1] + v[i2]) * s2 + v[i3]) ... ) * sk + v[i(k+1)])
            """
            assert len(idxs) == len(sizes) + 1

            def getter(flat_vars: list[sympy.Expr]) -> sympy.Expr:
                expr = flat_vars[idxs[0]]
                for s, idx in zip(sizes, idxs[1:]):
                    expr = s * expr + flat_vars[idx]
                return expr

            return getter

        return_getters_groups = []
        current_group = 0
        for length_group in lengths:
            return_getters = []
            for size in length_group:
                if sv.statically_known_equals(size, 1):  # type: ignore[arg-type]
                    return_getters.append(lambda _: sympy.S.Zero)
                    continue

                while current_group < len(remaining) and sv.statically_known_equals(
                    remaining[current_group],
                    1,  # type: ignore[arg-type]
                ):
                    # scroll to next group with remaining elements
                    current_group += 1

                # During native matmul on bmm, we enforce tiling order (z, y, x, r).
                # When fusing a bmm node with loop (z, y, x, r) with a pw node
                # of shape (z*y*x, 1), we need to split the pw iteration range
                # into three dimensions.
                # The group becomes [z, y, x, 1], with lengths ([z*y*x], []).
                # In this case, we decompose the combined size z*y*x into three
                # consecutive groups. Previously, _split_iteration_ranges supported
                # splitting into at most two dimensions, but we now extend it to do
                # three splits when the total size is divisible by all three.

                # is group having (z,y,x,r=1) form?
                is_bmm_then_pw = len(remaining) == 4 and remaining[-1] == 1
                if (
                    current_group + 2 < len(remaining)
                    and sv.statically_known_gt(
                        size, remaining[current_group] * remaining[current_group + 1]
                    )
                    and is_bmm_then_pw
                ):
                    # need to break size in three
                    if not sv.statically_known_multiple_of(
                        size, remaining[current_group] * remaining[current_group + 1]
                    ):
                        raise CantSplit(
                            size,
                            remaining[current_group] * remaining[current_group + 1],
                        )

                    size1 = remaining[current_group]
                    size2 = remaining[current_group + 1]
                    size3 = FloorDiv(size, size1 * size2)
                    return_getters.append(
                        # pyrefly: ignore [bad-argument-type]
                        make_combined(
                            [size2, size3],
                            [
                                add_range(current_group, size1),
                                add_range(current_group + 1, size2),
                                add_range(current_group + 2, size3),
                            ],
                        )
                    )

                # Two-dimensional tiling: split size across current_group and next group.
                elif current_group + 1 < len(remaining) and (
                    sv.statically_known_gt(size, remaining[current_group])
                    or
                    # statically_known_gt(size, remaining) may return False for symbolic
                    # expressions like 64*u0 vs u0, because both could be 0. Similarly for
                    # backed expressions like s25*(((s70 - 5)//4)) - s25 and
                    # (s25*(((s70 - 5)//4)) - s25)*64.
                    # We want to assume tensor sizes are not 0 and pass the gt
                    # using the following logic.
                    #
                    # if A//B = C and C >= 1
                    # then A = B * C + R
                    # and assuming A!=0
                    # A must be > B .
                    #
                    sv.statically_known_gt(FloorDiv(size, remaining[current_group]), 1)
                ):
                    # need to break size in two
                    if not sv.statically_known_multiple_of(
                        size, remaining[current_group]
                    ):
                        raise CantSplit(size, remaining[current_group])

                    size1 = remaining[current_group]
                    size2 = FloorDiv(size, remaining[current_group])
                    return_getters.append(
                        # pyrefly: ignore [bad-argument-type]
                        make_combined(
                            [size2],
                            [
                                add_range(current_group, size1),
                                add_range(current_group + 1, size2),
                            ],
                        )
                    )
                else:
                    if current_group >= len(remaining):
                        raise CantSplit(size, 0)
                    return_getters.append(
                        # pyrefly: ignore [bad-argument-type]
                        operator.itemgetter(add_range(current_group, size))
                    )
            return_getters_groups.append(return_getters)

        assert all(
            V.graph.sizevars.guarding_hint_or_throw(s) == 1 for s in remaining
        ), f"failed to set ranges {remaining} {lengths}"
        # pyrefly: ignore [bad-return]
        return new_ranges, return_getters_groups