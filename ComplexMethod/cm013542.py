def _refine_ranges(self, expr: SympyBoolean) -> None:
        expr = self.simplify(expr)

        for symbol in expr.free_symbols:
            if not isinstance(symbol, sympy.Symbol):
                raise AssertionError(f"Expected sympy.Symbol, got {type(symbol)}")

            if isinstance(self.backed_var_to_val.get(symbol, None), SingletonInt):
                # Skip var_to_range logic for SingletonInt which is only used
                # for jagged layout NestedTensors today
                continue

            r = try_solve(expr, symbol)

            if r is None or not (symbol.is_integer and r[1].is_integer):
                # Range refinement only supports integer symbols for now.
                # There are lots of SymPy bugs when it comes to comparing
                # reals and integers, so we skip that for now.
                continue

            r_expr, rhs = r
            vr = self.var_to_range[symbol]
            lower, upper = vr.lower, vr.upper

            rhs_vr = bound_sympy(rhs, self.var_to_range)

            # Let's suppose that we have a preexisting range for x [0, 100].
            # Now, we issue a guard x > y, where the range for y is [50, 150].
            # Then, lower = 0, rhs_vr.lower = 50 and therefore refinement can happen,
            # refining x to [51, 100], since x must be greater than y, but the lowest
            # y could be is 50.
            #
            # sympy.Eq may update both lower and upper bounds.
            # sympy.G{t,e} may update the lower bound, only.
            # sympy.L{t,e} may update the upper bound, only.
            if lower <= rhs_vr.lower and isinstance(
                r_expr, (sympy.Eq, sympy.Ge, sympy.Gt)
            ):
                # Strictly greater relations allow us to refine a bit more, since
                # x < y implies that the lower bound for x is: y + 1.
                lower = rhs_vr.lower + int(isinstance(r_expr, sympy.Gt))
            if upper >= rhs_vr.upper and isinstance(
                r_expr, (sympy.Eq, sympy.Le, sympy.Lt)
            ):
                upper = rhs_vr.upper - int(isinstance(r_expr, sympy.Lt))

            # Do nothing if the new value range is no better than what we already have.
            if vr == ValueRanges(lower, upper):
                continue

            # Updates the range and the guards corresponding to each bound of the symbol.
            self._update_var_to_range(symbol, ValueRanges(lower, upper))
            # If the range is refined to singleton, set replacement
            if self.var_to_range[symbol].is_singleton():
                self._set_replacement(
                    symbol,
                    self.var_to_range[symbol].lower,
                    "range_refined_to_singleton",
                )

            # Clears the cache, since this update can change the result.
            self._maybe_evaluate_static.cache_clear()