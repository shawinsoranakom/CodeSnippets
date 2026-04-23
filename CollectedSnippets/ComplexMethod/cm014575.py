def aliased_return_names(self) -> list[str | None]:
        outs: list[str | None] = []
        for r in self.returns:
            aliased_args = [
                a
                for a in self.arguments.flat_all
                if a.annotation is not None and a.annotation == r.annotation
            ]
            if len(aliased_args) == 0:
                outs.append(None)
            elif len(aliased_args) == 1:
                outs.append(aliased_args[0].name)
            else:
                aliased_names = ", ".join(a.name for a in aliased_args)
                raise AssertionError(
                    f"Found a return ({r.name})that aliases multiple inputs ({aliased_names})"
                )
        return outs