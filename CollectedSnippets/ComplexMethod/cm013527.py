def create_symfloatnode(
        self,
        sym: sympy.Expr,
        *,
        hint: int | float | bool | torch.SymInt | None,
        source: Source | None = None,
    ) -> FloatLikeType:
        """Create a SymFloat value from a symbolic expression"""
        if self._translation_validation_enabled and source is not None:
            # Create a new symbol for this source.
            symbol = self._create_symbol_for_source(source)
            if symbol is None:
                raise AssertionError("symbol must not be None")

            # Create a new FX placeholder and Z3 variable for 'symbol'.
            fx_node = self._create_fx_placeholder_and_z3var(symbol, float)

            # Add an equality assertion for the newly created symbol and 'sym'.
            self._add_assertion(sympy.Eq(symbol, sym))
        else:
            fx_node = None

        out: FloatLikeType
        if isinstance(sym, sympy.Float):
            if hint is not None:
                if float(sym) != hint:
                    raise AssertionError(f"float(sym)={float(sym)} != hint={hint}")
            out = float(sym)
        else:
            # You could give this the same treatment as SymInt above if
            # you supported mark_unbacked on a float, but it's a kind of
            # strange thing to do though because floats don't get 0/1
            # specialization anyway
            if free_unbacked_symbols(sym):
                if hint is not None:
                    raise AssertionError(
                        f"hint must be None for unbacked symbol: {sym}"
                    )
            out = SymFloat(SymNode(sym, self, float, hint, fx_node=fx_node))
        return out