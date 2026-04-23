def call_method(
        self,
        tx: "InstructionTranslator",
        name: str,
        args: list[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        from .constant import ConstantVariable
        from .dicts import HashableTracker

        # OrderedDict-exclusive C methods that ConstDictVariable doesn't handle.
        # https://github.com/python/cpython/blob/v3.13.0/Objects/odictobject.c
        if name == "move_to_end":
            assert self._base_vt is not None
            self._base_vt.install_dict_keys_match_guard()  # type: ignore[union-attr]
            tx.output.side_effects.mutation(self._base_vt)
            if args[0] not in self._base_vt:  # type: ignore[operator]
                raise_observed_exception(KeyError, tx)

            last = True
            if len(args) == 2 and args[0].is_python_constant():
                last = args[1].as_python_constant()
            if kwargs and "last" in kwargs and kwargs["last"].is_python_constant():
                last = kwargs["last"].as_python_constant()

            key = HashableTracker(args[0])
            self._base_vt.items.move_to_end(key, last=last)  # type: ignore[union-attr]
            return ConstantVariable.create(None)
        elif name == "popitem":
            assert self._base_vt is not None
            if not self._base_vt.items:  # type: ignore[union-attr]
                raise_observed_exception(
                    KeyError, tx, args=["popitem(): dictionary is empty"]
                )

            last = True
            if len(args) == 1 and args[0].is_python_constant():
                last = args[0].as_python_constant()
            if kwargs and "last" in kwargs and kwargs["last"].is_python_constant():
                last = kwargs["last"].as_python_constant()

            k, v = self._base_vt.items.popitem(last=last)  # type: ignore[union-attr]
            self._base_vt.should_reconstruct_all = True  # type: ignore[union-attr]
            tx.output.side_effects.mutation(self._base_vt)
            return variables.TupleVariable([k.vt, v])
        return super().call_method(tx, name, args, kwargs)