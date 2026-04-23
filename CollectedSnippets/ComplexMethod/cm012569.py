def indirect_assert(
        self,
        var: CSEVariable | str,
        lower: str | None,
        upper: str | None,
        mask: CSEVariable | str | None = None,
    ) -> str:
        if isinstance(var, CSEVariable):
            var = str(var)
        assert isinstance(var, str), type(var)
        assert lower is None or isinstance(lower, str)
        assert upper is None or isinstance(upper, str)
        if lower and upper:
            # The conditions need to be in parens because of Python's operator precedence.
            # It'd be less error-prone to use and/or/not, which is supported by triton
            cond = f"({lower} <= {var}) & ({var} < {upper})"
            cond_print = f"{lower} <= {var} < {upper}"
        elif lower:
            cond = f"{lower} <= {var}"
            cond_print = cond
        else:
            assert upper
            cond = f"{var} < {upper}"
            cond_print = cond

        if mask:
            cond = f"({cond}) | ~({mask})"

        return f'{self.assert_function}({cond}, "index out of bounds: {cond_print}")'