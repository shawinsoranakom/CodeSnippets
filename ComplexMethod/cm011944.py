def _stride_vars(
        self,
        index: Expr,
        vars: Sequence[sympy.Symbol],
        support_vars: Sequence[sympy.Symbol],
    ) -> list[Expr]:
        """Convert an indexing expression back into strides

        NOTE: This is only valid if the index is a standard strided offset
        calculation. e.g. 10 * ModularIndexing(i0 + 1, 1, 2) would give a
        stride of -10 because the index wraps around after the first element

        """
        strides = []
        index = self.simplify(index)
        # remove any offset
        index = index - sympy_subs(
            index, {v: sympy.S.Zero for v in support_vars if v != 0}
        )
        for i in range(len(vars)):
            # drop all the other dims
            index_dim = sympy_subs(
                index,
                {
                    support_vars[j]: sympy.S.Zero
                    for j in range(len(support_vars))
                    if vars[i] != support_vars[j] and support_vars[j] != 0
                },
            )
            v = vars[i]
            if v == 0:
                strides.append(sympy.S.Zero)
            else:
                # TODO(jansel): should we use sympy.diff here?
                strides.append(
                    sympy_subs(index_dim, {v: sympy.S.One})
                    - sympy_subs(index_dim, {v: sympy.S.Zero})
                )
        return strides