def _constrain_unify(self, a: SymInt, b: SymInt) -> None:
        """
        Given two SymInts, constrain them so that they must be equal.  NB:
        this will not work with SymInts that represent nontrivial expressions
        (yet!)
        """
        # TODO: this does not install a deferred runtime assert yet

        # TODO: Maybe dedupe this with _maybe_guard_rel?
        # Update Feb 2024: this is extra important to do, this doesn't handle
        # unbacked replacements properly nor does it generate deferred runtime
        # asserts
        if not isinstance(a, SymInt):
            if not isinstance(b, SymInt):
                if a != b:
                    raise AssertionError(f"Expected {a} == {b}")
            else:
                if not isinstance(b.node.expr, sympy.Symbol):
                    raise AssertionError("constraining non-Symbols NYI")
                if b.node.shape_env is not self:
                    raise AssertionError("b.node.shape_env must be self")
                self.replacements[b.node.expr] = sympy.Integer(a)
        else:
            # TODO: Actually, we can support this as long as one of them is a symbol.
            # NB: We can't actually do "unification" as our operators are not
            # injective
            if not isinstance(a.node.expr, sympy.Symbol):
                raise AssertionError("constraining non-Symbols NYI")
            if a.node.shape_env is not self:
                raise AssertionError("a.node.shape_env must be self")
            if not isinstance(b, SymInt):
                self.replacements[a.node.expr] = sympy.Integer(b)
            else:
                if a.node.shape_env is not b.node.shape_env:
                    raise AssertionError("a.node.shape_env must be b.node.shape_env")
                if not isinstance(b.node.expr, sympy.Symbol):
                    raise AssertionError("constraining non-Symbols NYI")
                new_var = self._find(a.node.expr)
                self.replacements[b.node.expr] = new_var