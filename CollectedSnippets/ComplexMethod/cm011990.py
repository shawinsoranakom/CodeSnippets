def get_free_symbol_uses(
        self, unbacked_only: bool = False
    ) -> OrderedSet[sympy.Symbol]:
        res = super().get_free_symbol_uses(unbacked_only)
        subgraph_outs = self.subgraph_outs if self.subgraph_outs else []
        subgraph_inps = self.subgraph_inps if self.subgraph_inps else []

        for inp in subgraph_inps:
            if isinstance(inp, sympy.Expr):
                res.update(get_free_symbols(inp, unbacked_only))
            elif isinstance(inp, IRNode):
                res.update(inp.get_free_symbol_uses(unbacked_only))
            else:
                assert inp is None

        for out in subgraph_outs:
            if isinstance(out, IRNode):
                res.update(out.get_free_symbol_uses(unbacked_only))
            else:
                assert out is None

        return res