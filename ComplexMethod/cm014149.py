def call_method(
        self,
        tx: "InstructionTranslator",
        name: str,
        args: list[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        if self.fn is object and name == "__setattr__":
            assert len(args) == 3
            assert len(kwargs) == 0
            obj, name_var, val = args
            obj = obj.realize()
            if (
                isinstance(obj, UserDefinedObjectVariable)
                and tx.output.side_effects.is_attribute_mutation(obj)
                and name_var.is_python_constant()
            ):
                return obj.method_setattr_standard(tx, name_var, val)

        if name == "__new__":
            # Supported __new__ methods
            if self.fn is object and len(args) == 1:
                assert len(kwargs) == 0
                return tx.output.side_effects.track_new_user_defined_object(
                    self, args[0], args[1:]
                )

            if (
                self.fn is tuple
                and len(args) == 2
                and args[1].has_force_unpack_var_sequence(tx)
                and not kwargs
            ):
                if isinstance(args[0], BuiltinVariable) and args[0].fn is tuple:
                    init_args = args[1].force_unpack_var_sequence(tx)
                    return variables.TupleVariable(
                        init_args, mutation_type=ValueMutationNew()
                    )

                return tx.output.side_effects.track_new_user_defined_object(
                    self,
                    args[0],
                    args[1:],
                )

        if name in _BUILTIN_CONSTANT_FOLDABLE_METHODS.get(self.fn, ()):
            if all(a.is_python_constant() for a in args) and all(
                v.is_python_constant() for v in kwargs.values()
            ):
                try:
                    fn = getattr(self.fn, name)
                    res = fn(
                        *(a.as_python_constant() for a in args),
                        **{k: v.as_python_constant() for k, v in kwargs.items()},
                    )
                    return VariableTracker.build(tx, res)
                except Exception as e:
                    raise_observed_exception(
                        type(e),
                        tx,
                        args=list(e.args),
                    )

        if self.fn is object and name == "__init__":
            # object.__init__ is a no-op
            return variables.ConstantVariable.create(None)

        if self.fn is set:
            resolved_fn = getattr(self.fn, name)
            if resolved_fn in set_methods:
                if isinstance(args[0], variables.UserDefinedSetVariable):
                    assert args[0]._base_vt is not None
                    return args[0]._base_vt.call_method(tx, name, args[1:], kwargs)
                elif isinstance(args[0], variables.SetVariable):
                    return args[0].call_method(tx, name, args[1:], kwargs)

        if self.fn is frozenset:
            resolved_fn = getattr(self.fn, name)
            if resolved_fn in frozenset_methods:
                if isinstance(args[0], variables.FrozensetVariable):
                    return args[0].call_method(tx, name, args[1:], kwargs)

        if self.fn is str and len(args) >= 1:
            resolved_fn = getattr(self.fn, name)
            if resolved_fn in str_methods:
                # Only delegate to ConstantVariable, not other types that happen to be constants
                if isinstance(args[0], ConstantVariable):
                    return args[0].call_method(tx, name, args[1:], kwargs)

        if self.fn is float and len(args) >= 1:
            # Only delegate to ConstantVariable, not other types that happen to be constants
            if isinstance(args[0], ConstantVariable):
                return VariableTracker.build(
                    tx, getattr(float, name)(args[0].as_python_constant())
                )

        if name == "__len__" and len(args) == 1 and not kwargs:
            # type.__len__(instance) → len(instance)
            # e.g. list.__len__(my_list) → len(my_list)
            from .object_protocol import generic_len

            return generic_len(tx, args[0])

        return super().call_method(tx, name, args, kwargs)