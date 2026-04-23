def call_set(
        self,
        tx: "InstructionTranslator",
        *args: VariableTracker,
        **kwargs: VariableTracker,
    ) -> VariableTracker:
        from .builder import SourcelessBuilder

        assert not kwargs
        if not args:
            return SetVariable([], mutation_type=ValueMutationNew())
        if len(args) != 1:
            raise_observed_exception(
                TypeError,
                tx,
                args=[f"set() takes 1 positional argument but {len(args)} were given"],
            )
        arg = args[0]
        if istype(arg, variables.SetVariable):
            return arg.clone(mutation_type=ValueMutationNew())
        elif arg.has_force_unpack_var_sequence(tx):
            items = arg.force_unpack_var_sequence(tx)
            return SetVariable(items, mutation_type=ValueMutationNew())
        elif isinstance(arg, variables.UserDefinedObjectVariable) and isinstance(
            arg.value, KeysView
        ):
            iter_fn = arg.var_getattr(tx, "__iter__")
            if isinstance(iter_fn, variables.UserMethodVariable):
                out = tx.inline_user_function_return(iter_fn, args, kwargs)
                if isinstance(out, SetVariable):
                    return out
                return SourcelessBuilder.create(tx, set).call_set(tx, out)
        raise_observed_exception(
            TypeError,
            tx,
            args=["failed to construct builtin set()"],
        )