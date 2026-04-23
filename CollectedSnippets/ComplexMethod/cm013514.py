def add(self, expr: SympyBoolean) -> bool:
        """Add an expression to the set of constraints.

        Return whether the expression is a trivial constraint (i.e., an obvious tautology).
        """
        if expr == sympy.true:
            return True
        orig_expr = expr
        orig_reduced = orig_expr.xreplace(self._var_to_val)
        # TODO(avik): https://github.com/pytorch/pytorch/issues/101093
        # It is possible that `expr` will fail the consistency check because of
        # precision errors. Specifically, on substituting its free symbols with
        # their concrete values, we might end up comparing floats. Until we have
        # a fix for this issue, we delay raising such failures. See solve().
        if orig_reduced == sympy.false:
            self._inconsistencies.append(f"{orig_expr} is inconsistent!")
        if isinstance(
            expr, (sympy.Ne, sympy.Or, sympy.And)
        ) or self._has_unsupported_sympy_function(expr):
            # we're not going to do anything useful with these, so drop them
            return False
        free_symbols = expr.free_symbols
        if not free_symbols:
            raise AssertionError(
                f"Did not expect constraint with no free variables: {expr}"
            )
        if len(free_symbols) > 1:
            # multivariate: record and move on
            self._multivariate_inequalities.add(expr)
        else:
            # univariate: can solve these immediately
            s = next(iter(free_symbols))
            # eliminate // and % (see documentation of `rewrite_with_congruences` above)
            old_n_congruences = len(self._congruences[s])
            expr = self.rewrite_with_congruences(s, expr)
            new_n_congruences = len(self._congruences[s])
            if expr == sympy.true:
                return old_n_congruences == new_n_congruences
            reduced = expr.xreplace(self._var_to_val)
            if reduced == sympy.false:
                self._inconsistencies.append(
                    f"{expr}, obtained by rewriting {orig_expr} with congruences, "
                    "is inconsistent!"
                )
            if isinstance(expr, sympy.Eq):
                # special status for symbols that have equalities (see `solve` below)
                self._symbols_with_equalities.add(s)
            self._univariate_inequalities[s].add(expr)
        return False