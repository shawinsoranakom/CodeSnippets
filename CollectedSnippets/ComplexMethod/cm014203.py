def _method_size_stride(
        self, name: str, dim: Any | None = None
    ) -> VariableTracker | None:
        dim = guard_if_dyn(dim)

        def make_const_size_variable(x: Sequence[Any], **options: Any) -> SizeVariable:
            return SizeVariable(
                [ConstantVariable.create(y, **options) for y in x], **options
            )

        RetVariable = (
            make_const_size_variable if name == "size" else ConstantVariable.create
        )

        # Technically, this should not be necessary, but I'm including it
        # for enhanced BC, in case example_value is sometimes not set
        # (it really should always be set though!)
        if name != "size":
            r = getattr(self, name)
        elif name == "size" and self.valid_size():
            r = self.size
        else:
            r = None

        if r is not None:
            if dim is None:
                return RetVariable(r)
            else:
                return ConstantVariable.create(r[dim])

        # It might still be constant!  Consult the fake tensor and see
        if (fake := self.proxy.node.meta.get("example_value")) is not None:
            if dim is None:
                fake_r = getattr(fake, name)()
                if not has_free_symbols(fake_r):
                    # int conversion for safety, in case a SymInt refined
                    # to constant
                    return RetVariable(tuple(int(r) for r in fake_r))
            else:
                fake_r = getattr(fake, name)(dim)
                if not has_free_symbols(fake_r):
                    return ConstantVariable.create(int(fake_r))
        return None