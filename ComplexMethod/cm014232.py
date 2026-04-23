def call_method(
        self,
        tx: "InstructionTranslator",
        name: str,
        args: list[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        if (
            name == "__init__"
            and (method := self._maybe_get_baseclass_method(name))
            and inspect.ismethoddescriptor(method)
            and len(kwargs) == 0
        ):
            return variables.ConstantVariable.create(None)
        elif (
            name == "__setattr__"
            and len(args) == 2
            and args[0].is_constant_match(
                "__cause__", "__context__", "__suppress_context__", "__traceback__"
            )
        ):
            self.exc_vt.call_setattr(tx, args[0], args[1])
        elif name == "with_traceback":
            return self.exc_vt.call_method(tx, name, args, kwargs)
        return super().call_method(tx, name, args, kwargs)