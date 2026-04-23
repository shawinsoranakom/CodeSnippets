def call_method(
        self,
        tx: "InstructionTranslator",
        name: str,
        args: list[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        from .constant import ConstantVariable

        if name == "__init__":
            # defaultdict.__init__(self, default_factory=None, *args, **kwargs)
            # https://github.com/python/cpython/blob/v3.13.3/Modules/_collectionsmodule.c#L2072
            # Extract default_factory, delegate rest to dict.__init__
            if len(args) >= 1:
                if self.is_supported_factory(args[0]):
                    self.default_factory = args[0]
                    tx.output.side_effects.store_attr(
                        self,
                        "default_factory",
                        self.default_factory,
                    )
                    args = list(args[1:])
                else:
                    # CPython raises TypeError for non-callable first arg
                    raise_observed_exception(
                        TypeError,
                        tx,
                        args=["first argument must be callable or None"],
                    )
            assert self._base_vt is not None
            return self._base_vt.call_method(tx, "__init__", args, kwargs)
        elif name == "__getitem__":
            if len(args) != 1:
                raise_args_mismatch(tx, name, "1 args", f"{len(args)} args")
            return self.mp_subscript_impl(tx, args[0])
        elif name == "__missing__":
            if len(args) != 1:
                raise_args_mismatch(tx, name, "1 args", f"{len(args)} args")
            return self._missing_impl(tx, args[0])
        elif name == "copy":
            # defaultdict.copy() creates a new defaultdict with same factory
            # https://github.com/python/cpython/blob/v3.13.3/Modules/_collectionsmodule.c#L2282
            from .builder import SourcelessBuilder

            assert self._base_vt is not None
            new_dd = tx.output.side_effects.track_new_user_defined_object(
                SourcelessBuilder.create(tx, dict),
                SourcelessBuilder.create(tx, collections.defaultdict),
                [],
            )
            assert isinstance(new_dd, DefaultDictVariable)
            new_dd.default_factory = self.default_factory
            new_dd._base_vt = self._base_vt.clone(
                mutation_type=ValueMutationNew(),
                source=None,
            )
            tx.output.side_effects.store_attr(
                new_dd, "default_factory", new_dd.default_factory
            )
            return new_dd
        elif name == "__setattr__":
            if len(args) != 2:
                raise_args_mismatch(tx, name, "2 args", f"{len(args)} args")
            if (
                istype(args[0], ConstantVariable) and args[0].value == "default_factory"
            ) and self.is_supported_factory(args[1]):
                self.default_factory = args[1]
                tx.output.side_effects.store_attr(
                    self, "default_factory", self.default_factory
                )
                return ConstantVariable.create(None)
            return super().call_method(tx, name, args, kwargs)
        elif name == "__eq__":
            if len(args) != 1:
                raise_args_mismatch(tx, name, "1 args", f"{len(args)} args")
            return VariableTracker.build(tx, polyfills.dict___eq__).call_function(
                tx, [self, args[0]], {}
            )
        return super().call_method(tx, name, args, kwargs)