def call_repr(
        self, tx: "InstructionTranslator", arg: VariableTracker
    ) -> VariableTracker | None:
        """Handle repr() on user defined objects."""
        if isinstance(
            arg,
            (variables.ExceptionVariable, variables.UserDefinedExceptionObjectVariable),
        ):
            try:
                const_args = tuple(a.as_python_constant() for a in arg.args)
            except NotImplementedError:
                return None
            if len(const_args) == 0:
                value = f"{arg.exc_type.__name__}()"
            elif len(const_args) == 1:
                value = f"{arg.exc_type.__name__}({const_args[0]!r})"
            else:
                value = f"{arg.exc_type.__name__}{const_args!r}"
            return VariableTracker.build(tx, value)
        if isinstance(arg, variables.UserDefinedDictVariable):
            assert arg._base_vt is not None
            try:
                return VariableTracker.build(
                    tx, repr(arg._base_vt.as_python_constant())
                )
            except Exception:
                pass
        if isinstance(arg, variables.UserDefinedObjectVariable):
            repr_method = arg.value.__repr__

            if type(arg.value).__repr__ is object.__repr__:
                # Default repr - build and trace it
                fn_vt = VariableTracker.build(tx, repr_method)
                return fn_vt.call_function(tx, [], {})
            elif is_wrapper_or_member_descriptor(repr_method):
                unimplemented(
                    gb_type="Attempted to call repr() method implemented in C/C++",
                    context="",
                    explanation=f"{type(arg.value)} has a C/C++ based repr method. This is not supported.",
                    hints=["Write the repr method in Python"],
                )
            else:
                bound_method = repr_method.__func__
                fn_vt = VariableTracker.build(tx, bound_method)
                return fn_vt.call_function(tx, [arg], {})
        if isinstance(arg, variables.UserDefinedClassVariable):
            if type(arg.value).__repr__ is type.__repr__:
                return VariableTracker.build(tx, repr(arg.value))
        if isinstance(
            arg,
            (
                RangeVariable,
                ConstDictVariable,
                variables.DefaultDictVariable,
                OrderedSetClassVariable,
                DictViewVariable,
            ),
        ):
            return VariableTracker.build(tx, arg.debug_repr())
        return None