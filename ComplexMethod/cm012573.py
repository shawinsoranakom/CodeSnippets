def indirect_indexing(
        self,
        var: CSEVariable,
        size: sympy.Expr | int,
        check: bool = True,
        wrap_neg: bool = True,
    ) -> sympy.Symbol:
        if isinstance(size, int):
            size = sympy.Integer(size)
        assert isinstance(size, sympy.Expr), (type(size), size)
        # Skip CSE since this doesn't return an expression

        if var.bounds.lower < 0:
            if wrap_neg:
                stm = ops.add(var, ops.index_expr(size, torch.long))
                # Mixed negative and non-negative
                if var.bounds.upper >= 0:
                    lt = ops.lt(var, 0)
                    stm = ops.where(lt, stm, var)
            else:
                stm = var

            # Propagate bounds as we know how to compute them properly
            new_bounds = ValueRanges.unknown()
            if var.bounds != ValueRanges.unknown() and isinstance(size, sympy.Number):
                # Take the negative part of the bound and add size to it
                # Then take union of that and the positive part
                # This is a tighter bound than that of a generic ops.where, as we have info on the cond
                neg_bounds = var.bounds & ValueRanges(-int_oo, -1)
                new_bounds = ValueRanges(
                    neg_bounds.lower + size, neg_bounds.upper + size
                )
                # We don't have a good way of representing the empty range
                if var.bounds.upper >= 0:
                    pos = var.bounds & ValueRanges(0, int_oo)
                    new_bounds = new_bounds | pos

            var = self.kernel.cse.generate(
                self.kernel.compute,
                stm,
                bounds=new_bounds,
                dtype=var.dtype,
                shape=var.shape,
            )

        sympy_var = self.parent_handler.indirect_indexing(var, size, check)
        if generate_assert(check):
            assert_lower = not (var.bounds.lower >= 0)
            # value ranges cannot x < s when x and s are symbols
            assert_upper = not isinstance(size, sympy.Number) or not (
                var.bounds.upper < size
            )
            self.kernel.check_bounds(sympy_var, size, assert_lower, assert_upper)
        return sympy_var