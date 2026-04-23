def _simplify_with_ranges(self, expr: Expr, var_ranges: VarRanges) -> Expr:
        """
        Simplify indexing expression with knowledge of the ranges of
        iteration variables.
        """

        expr = join_dimensions(self.simplify(expr))
        original_expr = expr

        var_to_range = dict(self.shape_env.var_to_range)
        var_to_range.update(
            {
                k: ValueRanges(
                    0, max(0, v - 1) if not has_free_symbols([v]) else IntInfinity()
                )
                for k, v in var_ranges.items()
            }
        )
        for var in expr.free_symbols:
            if var not in var_to_range:
                var_to_range[var] = ValueRanges(0, IntInfinity())

        var_to_range_tuple = cast(
            tuple[tuple[sympy.Symbol, ValueRanges[sympy.Expr]]],
            tuple(var_to_range.items()),
        )

        axioms = []
        for var, upper_bound in var_ranges.items():
            axioms.append(0 <= var)
            axioms.append(var < upper_bound)
        axioms = tuple(axioms) + self.shape_env.get_axioms()

        def statically_known(expr):
            evaluated = self.shape_env._maybe_evaluate_static(
                expr,
                # pyrefly: ignore [bad-argument-type]
                axioms=axioms,
                var_to_range=var_to_range_tuple,
            )
            return bool(evaluated)

        def remove_zero_terms(base, divisor):
            """Symbols smaller than the divisor are zero"""
            if not statically_known(base >= 0):
                return base

            for v in base.free_symbols:
                if v in var_ranges:
                    rest = sympy.Wild("_rest", exclude=[v])
                    m = base.match(v + rest)
                    if m and v not in m[rest].free_symbols:
                        # v can be removed if it doesn't affect the FloorDiv.
                        # rest is always a multiple of gcd(rest, divisor), so
                        # rest % divisor is also a multiple of that gcd. The
                        # worst case is rest % divisor == divisor - gcd, so
                        # adding v is safe when v < gcd.
                        gcd = sympy.gcd(m[rest], divisor)
                        if statically_known(v < gcd):
                            base = m[rest]
            return base

        def visit_indexing_div(base, divisor):
            base = remove_zero_terms(base, divisor)
            if statically_known(base >= 0) and statically_known(base < divisor):
                return sympy.S.Zero
            # FloorDiv(ModularIndexing(b, d1, m), d2) = ModularIndexing(b, d1*d2, m//d2)
            if isinstance(base, ModularIndexing) and isinstance(divisor, sympy.Integer):
                b, d1, m = base.args
                if m % divisor == 0:
                    return ModularIndexing(b, d1 * divisor, FloorDiv(m, divisor))
            return FloorDiv(base, divisor)

        def visit_modular_indexing(base, divisor, modulus):
            base = remove_zero_terms(base, divisor)

            can_remove_mod = statically_known(base >= 0) and statically_known(
                base < modulus * divisor
            )

            if can_remove_mod:
                return FloorDiv(base, divisor)
            return ModularIndexing(base, divisor, modulus)

        if expr.has(ModularIndexing):
            expr = expr.replace(
                ModularIndexing(
                    sympy.Wild("base", integer=True),
                    sympy.Wild("divisor", integer=True),
                    sympy.Wild("modulus", integer=True),
                ),
                visit_modular_indexing,
            )

        if expr.has(FloorDiv):
            expr = expr.replace(
                FloorDiv(
                    sympy.Wild("base", integer=True),
                    sympy.Wild("divisor", integer=True),
                ),
                visit_indexing_div,
            )

        if expr != original_expr:
            return self._simplify_with_ranges(expr, var_ranges)
        return expr