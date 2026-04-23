def _print_Pow(self, expr: sympy.Expr) -> str:
        # Uses float constants to perform FP div
        base, exp = expr.args

        if exp == 0.5 or exp == -0.5:
            # pyrefly: ignore [missing-attribute]
            base = self._print(base)
            return f"std::sqrt({base})" if exp == 0.5 else f"1.0/std::sqrt({base})"
        if exp.is_integer:
            exp = int(exp)
            if exp > 0:
                r = self.stringify([base] * exp, "*", PRECEDENCE["Mul"])
            elif exp < -1:
                r = (
                    "1.0/("
                    + self.stringify([base] * abs(exp), "*", PRECEDENCE["Mul"])
                    + ")"
                )
            elif exp == -1:
                # pyrefly: ignore [missing-attribute]
                r = "1.0/" + self._print(base)
            else:  # exp == 0
                r = "1.0"

            return f"static_cast<{INDEX_TYPE}>({r})" if expr.is_integer else r
        else:
            # TODO: float vs double
            return f"std::pow({base}, {float(exp)})"