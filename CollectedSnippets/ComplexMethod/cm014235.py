def __init__(
        self, value: object, set_vt: SetVariable | None = None, **kwargs: Any
    ) -> None:
        from .builder import SourcelessBuilder

        tx = kwargs.pop("tx", None)
        super().__init__(value, **kwargs)

        python_type = set if isinstance(value, set) else frozenset
        self._base_methods = set_methods if python_type is set else frozenset_methods

        if set_vt is None:
            assert self.source is None, (
                "set_vt must be constructed by builder.py when source is present"
            )
            if python_type is set:
                # set is initialized later
                self._base_vt = variables.SetVariable(
                    set(),
                    mutation_type=ValueMutationNew(),
                )
            else:
                init_args = kwargs.get("init_args", {})
                if tx is None:
                    tx = torch._dynamo.symbolic_convert.InstructionTranslator.current_tx()
                self._base_vt = SourcelessBuilder.create(tx, python_type).call_function(  # type: ignore[assignment]
                    tx, init_args, {}
                )
        else:
            self._base_vt = set_vt
        assert self._base_vt is not None