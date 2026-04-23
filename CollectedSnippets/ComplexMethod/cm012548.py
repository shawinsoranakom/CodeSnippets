def index_str(self, replacements=None, zero_vars=False):
        assert self.expr is not None
        expr = self.expr
        if zero_vars and expr == 0:
            return "hl.Var()"
        if replacements:
            replacements = {**replacements}
            # pyrefly: ignore [missing-attribute]
            for sym in expr.free_symbols:
                if symbol_is_type(sym, SymT.TMP):
                    assert isinstance(sym, sympy.Symbol)
                    var = V.kernel.lookup_cse_var(sym.name)
                    assert isinstance(var, HalideCSEVariable)
                    replacements[sym] = sympy_index_symbol(var.subs_str(replacements))
            expr = sympy_subs(expr, replacements)
        return V.kernel.index_to_str(expr)