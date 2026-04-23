def CALL_FUNCTION_EX(self, inst: Instruction) -> None:
        kwargsvars: VariableTracker
        if inst.argval == 0:
            kwargsvars = ConstDictVariable({})
            argsvars = self.pop()
        elif inst.argval == 1 or sys.version_info >= (3, 14):
            # Python 3.14+ removed the argval and replaced it with a possibly NULL kwargs
            kwargsvars = self.pop()
            if isinstance(kwargsvars, NullVariable):
                kwargsvars = ConstDictVariable({})
            argsvars = self.pop()
        else:
            unimplemented(
                gb_type="Variadic function call with bad flags",
                context=f"flags: {inst.argval}",
                explanation=f"Attempted to call a variadic function (CALL_FUNCTION_EX) with bad flags {inst.argval}",
                hints=[*graph_break_hints.DYNAMO_BUG],
            )

        if sys.version_info >= (3, 13):
            # 3.13 swapped null and callable
            null = self.pop()
            assert isinstance(null, NullVariable)

        fn = self.pop()

        if sys.version_info >= (3, 11) and sys.version_info < (3, 13):
            null = self.pop()
            assert isinstance(null, NullVariable)

        if not isinstance(
            argsvars,
            BaseListVariable,
        ) and argsvars.has_force_unpack_var_sequence(self):
            argsvars = TupleVariable(argsvars.force_unpack_var_sequence(self))

        # Unpack for cases like fn(**obj) where obj is a map
        if isinstance(kwargsvars, UserDefinedObjectVariable):
            kwargsvars = DictBuiltinVariable.call_custom_dict(self, dict, kwargsvars)  # type: ignore[arg-type]

        # pyrefly: ignore [unbound-name]
        if not isinstance(argsvars, BaseListVariable) or not isinstance(
            # pyrefly: ignore [unbound-name]
            kwargsvars,
            ConstDictVariable,
        ):
            unimplemented(
                gb_type="Variadic function call with bad args/kwargs type",
                # pyrefly: ignore [unbound-name]
                context=f"args type: {typestr(argsvars)}, kwargs type: {typestr(kwargsvars)}",
                explanation="Expected args to be a list and kwargs to be a dict",
                hints=[*graph_break_hints.USER_ERROR],
            )

        # Map to a dictionary of str -> VariableTracker
        # pyrefly: ignore [bad-assignment, unbound-name]
        kwargsvars = kwargsvars.keys_as_python_constant()
        # pyrefly: ignore [bad-argument-type, unbound-name]
        self.call_function(fn, argsvars.items, kwargsvars)