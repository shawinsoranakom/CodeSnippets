def _simplify_loops_impl(
        self, index_vars: list[sympy.Symbol], sizes, index_formulas
    ):
        """
        Try to remove as many axis from loop iterations as possible, by:
            1) removing size==1 dimensions
            2) fuse contiguous dimensions into a single loop
            If channel_last = True, we will prevent the last dim fused with other dims
        """
        sizes = list(map(self.simplify, sizes))

        strides = [
            # index_formulas may contain boolean expressions (e.g. s0 < 10),
            # for which "strides" don't make sense so we ignore them here.
            # NOTE: These expressions may still block merging dims in the sound
            # substitution test performed in can_merge_dims.
            (
                self.stride_vars(x, index_vars)
                if isinstance(x, sympy.Expr)
                else [0] * len(index_vars)
            )
            for x in index_formulas
        ]
        assert len(sizes) == len(strides[0]), (len(sizes), len(strides[0]))

        for i in range(len(sizes)):
            if sizes[i] == 1:
                # remove dim
                sizes[i] = None

        def can_merge_dims(a, b):
            for k in range(len(strides)):
                if self.simplify(strides[k][a] * sizes[a]) == self.simplify(
                    strides[k][b]
                ):
                    # approximate test passed, try sound version
                    va = index_vars[a]
                    vb = index_vars[b]
                    m1 = sympy_index_symbol("_merge_tester1")
                    m2 = sympy_index_symbol("_merge_tester2")
                    # NOTE: can't sub vb=0 here in case va * vb appears in the expression,
                    # in which case both expr1 and expr2 would be zero!
                    expr1 = sympy_subs(index_formulas[k], {va: m1 * sizes[a], vb: m2})
                    expr2 = sympy_subs(index_formulas[k], {va: 0, vb: (m1 + m2)})
                    if self.simplify(expr1) == self.simplify(expr2):
                        continue
                return False
            return True

        changed = True
        while changed:
            changed = False
            for i, j in itertools.product(
                reversed(range(len(sizes))), reversed(range(len(sizes)))
            ):
                if i == j or sizes[i] is None or sizes[j] is None:
                    continue
                if can_merge_dims(i, j):
                    changed = True
                    sizes[i] = sizes[i] * sizes[j]
                    sizes[j] = None

        def reindex(index):
            it = list(reversed(index))
            new_index = []
            for size in sizes:
                if size is None:
                    new_index.append(sympy.S.Zero)
                else:
                    new_index.append(it.pop())
            assert not it
            return new_index

        def prune(index):
            assert len(index) == len(sizes)
            return [i for i, s in zip(index, sizes) if s is not None]

        return [x for x in sizes if x is not None], reindex, prune