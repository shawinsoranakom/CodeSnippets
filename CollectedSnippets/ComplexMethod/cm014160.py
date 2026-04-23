def call_method(
        self,
        tx: "InstructionTranslator",
        name: str,
        args: list[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        if name == "__new__":
            if args:
                # dict.__new__ (tp_new) ignores extra args — only the first
                # arg (the type) matters.  Pass init_args=[] so reconstruction
                # emits base_cls.__new__(cls) without extras.
                # https://github.com/python/cpython/blob/v3.13.0/Objects/dictobject.c#L4735-L4768
                dict_vt = ConstDictVariable({}, dict, mutation_type=ValueMutationNew())
                if isinstance(args[0], DictBuiltinVariable):
                    return dict_vt
                return tx.output.side_effects.track_new_user_defined_object(
                    self, args[0], []
                )

        if name == "fromkeys":
            return DictBuiltinVariable.call_custom_dict_fromkeys(
                tx, dict, *args, **kwargs
            )

        resolved_fn = getattr(dict, name, None)
        if resolved_fn is not None and resolved_fn in dict_methods:
            if isinstance(args[0], variables.UserDefinedDictVariable):
                assert args[0]._base_vt is not None
                return args[0]._base_vt.call_method(tx, name, args[1:], kwargs)
            elif isinstance(args[0], ConstDictVariable):
                return args[0].call_method(tx, name, args[1:], kwargs)

        return super().call_method(tx, name, args, kwargs)