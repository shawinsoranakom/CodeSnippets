def check_remaining_star(self, lineno: int | None = None) -> None:
        assert isinstance(self.function, Function)

        if self.keyword_only:
            symbol = '*'
        elif self.deprecated_positional:
            symbol = '* [from ...]'
        else:
            return

        for p in reversed(self.function.parameters.values()):
            if self.keyword_only:
                if p.kind in {
                    inspect.Parameter.KEYWORD_ONLY,
                    inspect.Parameter.VAR_POSITIONAL,
                    inspect.Parameter.VAR_KEYWORD
                }:
                    return
            elif self.deprecated_positional:
                if p.deprecated_positional == self.deprecated_positional:
                    return
            break

        fail(f"Function {self.function.name!r} specifies {symbol!r} "
             f"without following parameters.", line_number=lineno)