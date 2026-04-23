def call_str(
        self, tx: "InstructionTranslator", arg: VariableTracker
    ) -> VariableTracker | None:
        if isinstance(
            arg,
            (variables.ExceptionVariable, variables.UserDefinedExceptionObjectVariable),
        ):
            if len(arg.args) == 0:
                return VariableTracker.build(tx, "")
            elif len(arg.args) == 1:
                return BuiltinVariable(str).call_function(tx, [arg.args[0]], {})
            else:
                tuple_var = variables.TupleVariable(list(arg.args))
                return BuiltinVariable(str).call_function(tx, [tuple_var], {})

        # Handle `str` on a user defined function or object
        if isinstance(arg, (variables.UserFunctionVariable)):
            return VariableTracker.build(tx, str(arg.fn))
        elif isinstance(arg, (variables.UserDefinedObjectVariable)):
            # Check if object has __str__ method
            if hasattr(arg.value, "__str__"):
                str_method = arg.value.__str__
            elif hasattr(arg.value, "__repr__"):
                # account for __repr__ functions when __str__ is absent
                str_method = arg.value.__repr__
            else:
                unimplemented(
                    gb_type="failed to call str() on user defined object",
                    context=str(arg),
                    explanation="User defined object has no __str__ or __repr__ method",
                    hints=[*graph_break_hints.USER_ERROR],
                )

            if type(arg.value).__str__ is object.__str__:
                # Rely on the object str method
                try:
                    # pyrefly: ignore [unbound-name]
                    return VariableTracker.build(tx, str_method())
                except AttributeError:
                    # Graph break
                    return None
            elif is_wrapper_or_member_descriptor(str_method):
                unimplemented(
                    gb_type="Attempted to a str() method implemented in C/C++",
                    context="",
                    explanation=f"{type(arg.value)} has a C/C++ based str method. This is not supported.",
                    hints=["Write the str method in Python"],
                )
            else:
                # Overrides for custom str method
                # Pass method as function to call tx.inline_user_function_return
                bound_method = str_method.__func__  # type: ignore[attr-defined]

                try:
                    # Only supports certain function types
                    user_func_variable = VariableTracker.build(tx, bound_method)
                except AssertionError:
                    # Won't be able to do inline the str method, return to avoid graph break
                    log.warning("Failed to create UserFunctionVariable", exc_info=True)
                    return None

                # Inline the user function
                return user_func_variable.call_function(tx, [arg], {})
        return None