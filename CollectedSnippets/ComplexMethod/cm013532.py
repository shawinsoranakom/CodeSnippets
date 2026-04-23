def _maybe_evaluate_static(
        self,
        expr: sympy.Basic,
        *,
        unbacked_only: bool = False,
        compute_hint: bool = False,
        size_oblivious: bool = False,
        axioms: tuple[SympyBoolean] | None = None,
        var_to_range: tuple[tuple[sympy.Symbol, ValueRanges[sympy.Expr]]] | None = None,
    ) -> sympy.Basic | None:
        """
        Tries to evaluate expr without introducing guards

        If unbacked_only == True, then we only do substitutions on
        unbacked SymInts (leaving regular hinted integers alone).  This could
        result in an expression that still contains backed SymInts, which you
        could then potentially guard on.

        Use compute_hint == True if you are trying to compute a non-binding
        hint for the particular hint values of backed and unbacked SymInts,
        e.g., if s0 happens to be 3 this run, compute_hint will substitute s0 with 3.
        """

        # axioms with compute hint NYE
        if compute_hint and axioms:
            raise AssertionError("compute_hint and axioms cannot both be set")
        expr = self.simplify(expr, size_oblivious)

        if compute_hint:
            expr = expr.xreplace(self.backed_var_to_val).xreplace(
                self.real_tensor_prop_unbacked_vals
            )

        expr = canonicalize_bool_expr(expr)

        def resimplify_floor_div(axioms: dict[sympy.Expr, sympy.Expr]) -> None:
            if not self._resimplify_floor_div_axioms:
                return
            self._resimplify_floor_div_axioms = False
            new_items = {}
            for k, v in list(axioms.items()):
                # A FloorDiv in implications could have became CleanDiv at this point, due to new facts
                # to the shapeEnv. This handles such issue but its not ideal. This is the only expression
                # simplification that depends on the global state of shape env.
                # TODO try to get rid of CleanDiv since it breaks the invariant that's simplifications of sympy
                # expressions only depend on the expression itself.
                if k.has(FloorDiv):
                    new_items.update({self.simplify(k): v})
            axioms.update(new_items)

        # Pattern matching
        if axioms is None:
            resimplify_floor_div(self.axioms)
            subst = self.axioms
        else:
            subst = {}
            for e in axioms:
                if e.free_symbols.issubset(expr.free_symbols):
                    subst.update(dict(self.get_implications(self.simplify(e))))

            resimplify_floor_div(subst)

        expr = expr.xreplace(subst)
        # TODO: compute hint might have gotten broken here

        fs = expr.free_symbols

        if not fs and (expr.is_number or expr.is_Boolean):
            return expr

        if var_to_range is None:
            var_ranges = self.var_to_range
        else:
            var_ranges = dict(var_to_range)

        symbol_info = tuple(
            _SymbolInfo(
                s,
                var_ranges.get(s),
                self.backed_var_to_val.get(s),
                s in self.size_like,
            )
            for s in sorted(fs, key=str)  # TODO: speed up sort?
        )

        r = _maybe_evaluate_static_worker(
            expr, symbol_info, unbacked_only, size_oblivious
        )
        return r