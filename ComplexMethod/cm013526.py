def create_symintnode(
        self,
        sym: sympy.Expr,
        *,
        hint: int | float | bool | torch.SymInt | None,
        source: Source | None = None,
    ) -> IntLikeType:
        """Create a SymInt value from a symbolic expression

        If you know what the current hint value of the SymInt to be created
        is, pass it into hint.  Otherwise, pass None and we will make our best
        guess

        """
        if self._translation_validation_enabled and source is not None:
            # Create a new symbol for this source.
            symbol = self._create_symbol_for_source(source)
            if symbol is None:
                raise AssertionError("symbol must not be None")

            # Create a new FX placeholder and Z3 variable for 'symbol'.
            fx_node = self._create_fx_placeholder_and_z3var(symbol, int)

            # Add an equality assertion for the newly created symbol and 'sym'.
            self._add_assertion(sympy.Eq(symbol, sym))
        else:
            fx_node = None

        out: IntLikeType
        if isinstance(sym, sympy.Integer):
            if hint is not None:
                if int(sym) != hint:
                    raise AssertionError(f"int(sym)={int(sym)} != hint={hint}")
            out = int(sym)
        else:
            # How can this occur? When we mark_unbacked, we end up with a real
            # tensor that has hints for all sizes, but we MUST NOT create a
            # SymNode with a hint, because we're hiding the hint from our eyes
            # with the unbacked Symbol.  And in fact, the hint compute may be
            # inconsistent with size oblivious tests.
            if free_unbacked_symbols(sym):
                hint = None
            out = SymInt(SymNode(sym, self, int, hint, fx_node=fx_node))
        return out