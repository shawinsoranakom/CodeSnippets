def _init_cls(cls):
        """
        Here we codegen many functions of the form:

            def add(self, a, b):
                return self._default('add', (a, b), {})

        and install them in cls.  This is the same as _call_default above,
        but is about 1.2x faster since CPython varargs parsing is slow.
        """
        code = StringIO()
        for target in OP_NAMES:
            sig = inspect.signature(getattr(OpsHandler, target))
            if all(
                p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
                and p.default is inspect.Parameter.empty
                for p in sig.parameters.values()
            ):
                self_arg, *args = sig.parameters.keys()
                assert self_arg == "self"
                code.write(
                    f"""
                    def {target}(self, {", ".join(args)}):
                        return self._default({target!r}, ({", ".join(args)}, ), {{}})
                    """.strip()
                )
                code.write("\n\n")
            else:
                # slower fallback for ops with default or variadic arguments
                setattr(cls, target, cls._call_default(target))

        ctx: dict[str, Any] = {}
        exec(code.getvalue(), ctx)
        for target, impl in ctx.items():
            if target in OP_NAMES:
                setattr(cls, target, impl)