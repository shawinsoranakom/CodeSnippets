def __init__(
        self,
        items: Sequence[VariableTracker],
        tx: Optional["InstructionTranslator"] = None,
        **kwargs: Any,
    ) -> None:
        items_to_map = items
        start, stop, step = [variables.ConstantVariable.create(None)] * 3

        if len(items_to_map) == 1:
            (stop,) = items_to_map
        elif len(items_to_map) == 2:
            start, stop = items_to_map
        elif len(items_to_map) == 3:
            start, stop, step = items_to_map
        else:
            raise AssertionError

        # Convert TensorVariable to SymIntVariable by calling .item()
        # This decomposes a[:t] to u=t.item(); a[:u] at the dynamo level
        if start.is_tensor():
            assert tx is not None, (
                "tx is required when slice indices are TensorVariables"
            )
            start = start.call_method(tx, "item", [], {})
        if stop.is_tensor():
            assert tx is not None, (
                "tx is required when slice indices are TensorVariables"
            )
            stop = stop.call_method(tx, "item", [], {})
        if step.is_tensor():
            assert tx is not None, (
                "tx is required when slice indices are TensorVariables"
            )
            step = step.call_method(tx, "item", [], {})

        self.items = (start, stop, step)

        super().__init__(**kwargs)