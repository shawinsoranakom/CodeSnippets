def solve(self) -> None:
        """Solve the system of constraint equations to find simplified constraints"""
        self._raise_inconsistencies()
        # as long as there are symbols with equalities, solve for them
        # NOTE(avik): this is guaranteed to terminate (#iterations <= #symbols)
        while self._symbols_with_equalities:
            s = self._symbols_with_equalities.pop()
            exprs = self._univariate_inequalities.pop(s)
            solution = sympy.solvers.inequalities.reduce_inequalities(exprs, s)
            if isinstance(solution, sympy.And):
                solution = next(
                    (arg for arg in solution.args if isinstance(arg, sympy.Eq)),
                    solution,
                )
                if not isinstance(solution, sympy.Eq):
                    raise AssertionError(
                        f"Expected an equality constraint for {s}, got {solution}"
                    )
            symbol, val = solution.args
            if symbol != s:
                raise AssertionError(
                    f"Expected a constraint on {s} instead of on {symbol}"
                )
            # because this is univariate, the solution is a specialization
            self._static_results.add(
                f"{self._dcp.symbol_to_source[s][0].name} == {val}"
            )
            # add this as a substitution to simplify other constraints
            self._substitutions[s] = val  # type: ignore[assignment]

            # simplify multivariate inequalities: some of them will now become univariate!
            multivariate_inequalities = self._multivariate_inequalities
            self._multivariate_inequalities = set()
            for expr in multivariate_inequalities:
                self.add(expr.xreplace({s: self._substitutions[s]}))
            self._raise_inconsistencies()

        # solve linear congruences
        # NOTE(avik): We do not need to solve them for symbols that have already been specialized.
        reduced_congruences = self._reduce_congruences()
        for s, congruences in reduced_congruences.items():
            for congruence in congruences:
                # any congruence that cannot be checked becomes a dynamic constraint as well
                if s not in self._substitutions or not sympy.checksol(
                    congruence, {s: self._substitutions[s]}
                ):
                    if self._is_supported_congruence(congruence):
                        base, divisor = congruence.args
                        tmp_name = "_" + str(
                            self._dcp.source_name_to_debug_name.get(
                                self._dcp.symbol_to_source[s][0].name,
                                self._dcp.symbol_to_source[s][0].name,
                            )
                        )
                        tmp = sympy.Symbol(tmp_name, integer=True)
                        from torch._dynamo.source import ConstantSource

                        self._dcp.symbol_to_source[tmp] = [ConstantSource(tmp_name)]
                        r = try_solve(sympy.Eq(base, divisor * tmp), s)
                        if r is None:
                            raise AssertionError(
                                f"Failed to solve {base} = {divisor} * {tmp} for {s}"
                            )
                        self._dynamic_results.add(self._dcp.doprint(sympy.Eq(s, r[1])))

        # remaining symbols have only pure inequalities (no equalities)
        for s, exprs in self._univariate_inequalities.items():
            try:
                solution = sympy.solvers.inequalities.reduce_inequalities(exprs, s)
                # because this is univariate, the solution is a dynamic (range) constraint
                if isinstance(solution, sympy.Or):
                    solution = next(
                        iter(
                            arg
                            for arg in solution.args
                            if arg.xreplace(self._var_to_val)
                        )
                    )
                if isinstance(solution, sympy.And):
                    for arg in solution.args:
                        self._dynamic_results.add(self._dcp.doprint(arg))
                else:
                    self._dynamic_results.add(self._dcp.doprint(solution))
            except (NotImplementedError, AssertionError):
                log.warning("Failed to reduce inequalities", exc_info=True)
                for expr2 in exprs:
                    self._dynamic_results.add(self._dcp.doprint(expr2))

        # simplify symbolic equivalences: some of them will now become specializations!
        symbolic_equivalences = self._symbolic_equivalences
        self._symbolic_equivalences = []
        for source, expr3 in symbolic_equivalences:
            self.add_equality(source, expr3.xreplace(self._substitutions))

        # remaining symbolic equivalences become dynamic equality constraints
        for source, expr3 in self._symbolic_equivalences:
            self._dynamic_results.add(f"{source.name} == {self._dcp.doprint(expr3)}")