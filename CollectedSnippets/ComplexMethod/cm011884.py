def register(
        self,
        pass_dicts: _PassDictsType | Sequence[_PassDictsType],
        target: torch.fx.node.Target | None = None,
        prepend: bool = False,
    ) -> None:
        if target is None:
            assert hasattr(self.pattern, "fns")
            for fn in self.pattern.fns:
                self.register(pass_dicts, fn, prepend=prepend)
        elif isinstance(pass_dicts, (dict, PatternMatcherPass)):
            assert hasattr(self.pattern, "op")
            if prepend:
                pass_dicts[(self.pattern.op, target)].insert(0, self)
            else:
                pass_dicts[(self.pattern.op, target)].append(self)
        else:
            pass_dicts = typing.cast(Sequence[_PassDictsType], pass_dicts)
            for x in pass_dicts:
                self.register(x, target, prepend=prepend)