def add_list_construct(self, node):
        if node.outputsSize() != 1:
            raise AssertionError(
                f"expected node.outputsSize() == 1, got {node.outputsSize()}"
            )
        output = node.outputsAt(0)
        ctype = output.type()
        const_vals: list | None = []
        tensors: list | None = []
        for inp in node.inputs():
            if const_vals is not None and inp in self.constants:
                _, val = self.get_constant_value(inp)
                const_vals.append(val)
            else:
                const_vals = None
            if tensors is not None and inp.type().kind() == "TensorType":
                tensors.append(inp)
            else:
                tensors = None

        if const_vals is not None:
            # NOTE: Now that TorchScript supports list constants,
            # this code path might not be used anymore.
            self.add_constant_value(output, ctype, const_vals)
        if tensors is not None:
            self.add_tensor_sequence(output, tensors)
        if const_vals is None and tensors is None:
            raise Exception(  # noqa: TRY002
                f"Unable to handle ListConstruct node.  Neither all constants nor all tensors. {node!r}"
            )