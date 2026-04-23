def _should_skip_static_eval(self, expr: SympyBoolean) -> bool:
        """Check if we should skip _maybe_evaluate_static for the given expression.

        Skips static evaluation for single unbacked symbol >= 0 (or 0 <= symbol)
        when the symbol has unknown range [-int_oo, int_oo].
        This pattern is common during tracing and doesn't benefit from static evaluation
        since the symbol has no constraints.
        Note that the first time this is called value range will be updated and next time
        it's called (if any) we would call _maybe_evaluate_static and it would return True.
        """
        unbacked_sym = None
        if isinstance(expr, sympy.GreaterThan) and expr.rhs == 0:
            unbacked_sym = expr.lhs
        elif isinstance(expr, sympy.LessThan) and expr.lhs == 0:
            unbacked_sym = expr.rhs
        if isinstance(unbacked_sym, sympy.Symbol) and symbol_is_type(
            unbacked_sym, SymT.UNBACKED_INT
        ):
            vr = self.var_to_range[unbacked_sym]
            if vr.lower == -int_oo and vr.upper == int_oo:
                return True
        return False