def unpack_var_sequence(
        self, tx: "InstructionTranslator", idxes: Sequence[int] | None = None
    ) -> list[VariableTracker]:
        from .builder import wrap_fx_proxy_cls
        from .torch_function import TensorWithTFOverrideVariable

        if self.valid_size():
            size_len = len(self.size)
        else:
            size_var = self.call_method(tx, "size", [], {})
            assert isinstance(size_var, SizeVariable)
            size_len = len(size_var.items)
        # Ensure we don't unpack a scalar tensor.
        assert size_len != 0, "Can't unpack scalar tensors."

        if self.valid_size():
            length = self.size[0]
        else:
            dyn_length = self.call_method(
                tx, "size", [VariableTracker.build(tx, 0)], {}
            )
            # SymNodeVariable for symbolic sizes, ConstantVariable for constants OR values produced through
            # symbolic_shapes, but that end up as int/sympy.Integer
            assert (
                isinstance(dyn_length, SymNodeVariable)
                or dyn_length.is_python_constant()
            )
            if isinstance(dyn_length, SymNodeVariable):
                length = dyn_length.evaluate_expr(tx.output)
            else:
                length = dyn_length.as_python_constant()

        if idxes is None:
            idxes = range(length)  # type: ignore[arg-type]
        else:
            assert len(idxes) == length, (
                f"Can't unpack a tensor of {length} rows into a tuple of {len(idxes)} elements."
            )

        # preserve tensor subclass type when unpacking
        if isinstance(self, TensorWithTFOverrideVariable):
            base_vars = [
                wrap_fx_proxy_cls(
                    target_cls=TensorVariable, tx=tx, proxy=self.as_proxy()[i]
                )
                for i in idxes
            ]
            return [
                TensorWithTFOverrideVariable.from_tensor_var(
                    tx, v, self.class_type, self.source
                )
                for v in base_vars
            ]

        return [
            wrap_fx_proxy_cls(target_cls=type(self), tx=tx, proxy=self.as_proxy()[i])
            for i in idxes
        ]