def var_getattr(self, tx: "InstructionTranslator", name: str) -> VariableTracker:
        if name == "__class__":
            return VariableTracker.build(tx, self.exc_type)
        elif name == "__context__":
            return self.__context__
        elif name == "__cause__":
            return self.__cause__
        elif name == "__suppress_context__":
            return self.__suppress_context__
        elif name == "__traceback__":
            return self.__traceback__
        elif name == "args":
            return VariableTracker.build(
                tx,
                tuple(self.args),
                source=self.source and AttrSource(self.source, "args"),
            )
        return super().var_getattr(tx, name)