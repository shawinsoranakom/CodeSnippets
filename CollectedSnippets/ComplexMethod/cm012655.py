def prepare_indexing(
        self,
        index: sympy.Expr,
    ) -> sympy.Expr:
        index = self.simplify_indexing(index)
        index = sympy_subs(index, V.graph.sizevars.precomputed_replacements)
        # if simple replacements didn't get rid of floor/ceil, try full subs
        if len(index.atoms(sympy.floor)) or len(index.atoms(sympy.ceiling)):
            index = index.subs(V.graph.sizevars.precomputed_replacements)
        # last resort, if no range vars are in the expr, hoist it
        # TODO instead of trying to blindly find complicated exprs, we should hoist the
        # inputs/outputs sizes and strides, but at the time indexing is generated
        # kernel inputs and outputs are not set yet, we'd need a deeper refactor
        # to do it this way

        if len(index.atoms(sympy.ceiling)):
            for a in index.atoms(sympy.ceiling):
                # for nested exprs, atoms yields top level first (?)
                # so if everything goes fine, lower level replacements will come up empty
                symbols = a.free_symbols
                if len(symbols) > 0 and all(
                    symbol_is_type(s, (SymT.SIZE, SymT.PRECOMPUTED_SIZE))
                    for s in symbols
                ):
                    replacements = {a: V.graph.sizevars.lookup_precomputed_size(a)}
                    index = sympy_subs(index, replacements)

        simp_index = self.simplify_indexing(index)

        # Now that we are done simplifying we can unwrap Identity so that downstream handling
        # for its contained expression will work. previously, tl.full wrapping of sympy.Integer
        # would not occur
        simp_index = (
            simp_index if not isinstance(simp_index, Identity) else simp_index.args[0]
        )

        return self.codegen_indexing(simp_index)