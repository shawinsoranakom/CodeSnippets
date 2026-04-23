def _reduce_congruences(self) -> dict[sympy.Symbol, set[sympy.Expr]]:
        reduced_congruences: dict[sympy.Symbol, set[sympy.Expr]] = {}
        for s, congruences in self._congruences.items():
            remainder_modulus_pairs: list[tuple[sympy.Integer, sympy.Integer]] = []
            congruences_to_check = set()
            for congruence in congruences:
                base, divisor = congruence.args
                # We are given a congruence of the form base % divisor == 0 with a free variable s. So:
                # - we transform this into an equation of the form base = divisor * tmp;
                # - we solve this equation for s to get a linear solution with free variable tmp.
                tmp = sympy.Symbol("reduce_congruences_tmp", integer=True)
                symbol, solution = sympy.solve_linear(base - divisor * tmp, symbols=[s])
                # See https://docs.sympy.org/latest/modules/solvers/solvers.html#sympy.solvers.solvers.solve_linear
                # for how to interpret the results.
                if s == symbol:
                    # This means the solution is of the form s = modulus*tmp + remainder.
                    modulus, remainder = sympy.polys.polytools.div(solution, tmp)
                    if isinstance(modulus, sympy.Integer) and isinstance(
                        remainder, sympy.Integer
                    ):
                        # Make sure 0 <= remainder <= modulus.
                        remainder = remainder % modulus
                        remainder_modulus_pairs.append((remainder, modulus))
                        continue
                # This means that we did not get a unique solution to the equation.
                # No problem, we will check it.
                congruences_to_check.add(congruence)
            # Finally we solve for a congruence s such that s = r_i mod m_i for each (r_i, m_i).
            # The solution will be a congruence of the form s = r mod m.
            # NOTE(avik): Since the given m_i may not be pairwise coprime, we can't just use CRT.
            if remainder_modulus_pairs:
                remainder, modulus = sympy.ntheory.modular.solve_congruence(
                    *remainder_modulus_pairs
                )
                reduced_congruences[s] = {(s - remainder) % modulus}
                substitution = {
                    s: modulus * sympy.Symbol("tmp", integer=True) + remainder
                }
                reduced_congruences[s].update(
                    congruence
                    for congruence in congruences_to_check
                    if not sympy.checksol(congruence, substitution)
                )
            else:
                reduced_congruences[s] = congruences_to_check

        return reduced_congruences