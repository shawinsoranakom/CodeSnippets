def call_setattr(
        self,
        tx: "InstructionTranslator",
        name_var: VariableTracker,
        val: VariableTracker,
    ) -> VariableTracker:
        name = name_var.as_python_constant()
        if name == "__context__":
            # Constant can be either an Exceptior or None
            assert val.is_constant_none() or isinstance(
                val,
                (
                    variables.ExceptionVariable,
                    variables.UserDefinedExceptionClassVariable,
                    variables.UserDefinedExceptionObjectVariable,
                ),
            ), f"{val} is not a valid exception context"
            self.set_context(val)
        elif name == "__cause__":
            if val.is_constant_none() or isinstance(
                val,
                (
                    variables.BuiltinVariable,
                    variables.ExceptionVariable,
                    variables.UserDefinedExceptionClassVariable,
                    variables.UserDefinedExceptionObjectVariable,
                ),
            ):
                self.__cause__ = val
                self.__suppress_context__ = variables.ConstantVariable.create(True)
            else:
                raise_type_error(
                    tx, "exception cause must be None or derive from BaseException"
                )
        elif name == "__suppress_context__":
            if val.is_constant_match(True, False):
                self.__suppress_context__ = val
            else:
                raise_type_error(
                    tx, "exception cause must be None or derive from BaseException"
                )
        elif name == "__traceback__":
            if not TracebackVariable.is_valid_traceback(val):
                raise_type_error(tx, "__traceback__ must be a traceback object or None")
            self.__traceback__ = val
        else:
            unimplemented(
                gb_type="Unsupported attribute assignment on Exception object",
                context=f"call_setattr {self} {name}",
                explanation="Dynamo does not support setting the attribute "
                f"'{name}' on tracked exception objects. Only `__context__`, "
                "`__cause__`, `__suppress_context__`, and `__traceback__` are supported.",
                hints=[*graph_break_hints.SUPPORTABLE],
            )
        return variables.ConstantVariable.create(None)