def patch_source_specialization(
        self, source: Source, check_fn: Callable[[sympy.Symbol], sympy.Expr]
    ) -> Generator[None, None, None]:
        """
        Temporarily add symbol-level axioms to the ShapeEnv. This is useful when you want to "fork"
        and have parallel universes of ShapeEnvs. For example, we use this when doing multi-graph
        compile so we can support various graphs with varying levels of specializations.

        This context manager allows for temporarily adding constraints to the shape environment
        based on a specialization function applied to a symbol associated with a source.

        Args:
            source: The source of the symbol to specialize
            check_fn: A function that takes a sympy Symbol and returns a sympy expression
                     representing a constraint/specialization to be applied
        """
        name = source.name
        sym = self.source_to_var[name]
        expr = check_fn(SymInt(SymNode(sym, self, int, None))).node._expr
        new_axioms = dict(self.get_implications(self.simplify(expr)))
        added_replacements = {}

        for axiom in new_axioms:
            if (
                isinstance(axiom, sympy.Eq)
                and isinstance(axiom.lhs, sympy.Symbol)
                and isinstance(axiom.rhs, sympy.Integer)
                and axiom.lhs not in self.replacements
            ):
                self.replacements[axiom.lhs] = axiom.rhs
                added_replacements[axiom.lhs] = axiom.rhs
        self.axioms.update(new_axioms)

        # We need to freeze the ShapeEnv because any additional modification of
        # the ShapeEnv will cause unsoundness for subsequent specialization calls.
        self.frozen = True
        try:
            yield
        finally:
            for k in new_axioms:
                self.axioms.pop(k, None)
            for k in added_replacements:
                self.replacements.pop(k, None)
            self.frozen = False