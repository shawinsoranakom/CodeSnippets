def call_function(
        self,
        tx: "InstructionTranslator",
        args: Sequence[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        from .lazy import LazyVariableTracker

        if any(isinstance(a, LazyVariableTracker) for a in args):
            args = [
                a.realize() if isinstance(a, LazyVariableTracker) else a for a in args
            ]
        try:
            return self._call_getattr(tx, args, kwargs)
        except Unsupported:
            # Replicate the constant-fold fallback from BuiltinVariable._make_handler:
            # if all args are python constants, evaluate getattr() directly rather
            # than propagating a graph break from var_getattr.
            if not check_unspec_or_constant_args(args, kwargs):
                raise
            try:
                result = getattr(*[a.as_python_constant() for a in args])
            except AttributeError:
                raise_observed_exception(AttributeError, tx)
                raise
            except AsPythonConstantNotImplementedError:
                raise
            except Exception as exc:
                raise_observed_exception(type(exc), tx, args=list(exc.args))
                raise
            return VariableTracker.build(tx, result)