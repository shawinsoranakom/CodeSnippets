def get_axioms(
        self,
        symbols: tuple[sympy.Symbol] | None = None,
        compute_hint: bool = False,
    ) -> tuple[SympyBoolean, ...]:
        """
        Given the symbols in an expression, it returns all the runtime asserts that have those symbols
        concatenated with all the guards.
        If symbols is None, it returns all the runtime asserts (and all the guards)
        """
        if symbols is None:
            runtime_asserts = (
                r.expr for rs in self.deferred_runtime_asserts.values() for r in rs
            )
        else:
            runtime_asserts = (
                r.expr
                for s in symbols
                if s not in self.backed_var_to_val
                for r in self.deferred_runtime_asserts.get(s, ())
            )
        guards: Iterator[SympyBoolean] = (g.expr for g in self.guards)
        axioms: Iterator[SympyBoolean] = itertools.chain(guards, runtime_asserts)
        if compute_hint:
            axioms = (
                canonicalize_bool_expr(a.xreplace(self.backed_var_to_val))
                for a in axioms
            )
        return tuple(dict.fromkeys(axioms).keys())