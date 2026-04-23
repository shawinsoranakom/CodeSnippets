def unpack_var_sequence(self, tx: "InstructionTranslator") -> list[VariableTracker]:
        if self._base_vt is not None and self._base_methods is not None:
            iter_method = self._maybe_get_baseclass_method("__iter__")
            if iter_method is not None and iter_method in self._base_methods:
                return self._base_vt.unpack_var_sequence(tx)
        if (
            self.source
            and self._maybe_get_baseclass_method("__iter__") is list.__iter__
            and self._maybe_get_baseclass_method("__len__") is list.__len__
            and self._maybe_get_baseclass_method("__getitem__") is list.__getitem__
        ):
            install_guard(self.source.make_guard(GuardBuilder.SEQUENCE_LENGTH))
            return [
                variables.LazyVariableTracker.create(
                    self.value[k],  # type: ignore[index]
                    source=GetItemSource(self.source, k),
                )
                for k in range(len(self.value))  # type: ignore[arg-type]
            ]
        return super().unpack_var_sequence(tx)