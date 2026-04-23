def __init__(
        self, operation, call_args=None, call_kwargs=None, outputs=None
    ):
        self.operation = operation
        self.arguments = SymbolicArguments(*call_args, **call_kwargs)
        self.outputs = [] if outputs is None else tree.flatten(outputs)
        for x in self.outputs:
            if not isinstance(x, KerasTensor):
                raise ValueError(
                    "All operation outputs must be tensors. "
                    f"Operation {operation} returned a non-tensor. "
                    f"Non-tensor received: {x}"
                )

        zero_history = any(
            not x.record_history for x in self.arguments.keras_tensors
        )

        # If inputs don't have metadata yet, add it.
        if not zero_history:
            for tensor in self.arguments.keras_tensors:
                if not hasattr(tensor, "_keras_history"):
                    tensor._keras_history = KerasHistory(
                        operation=None, node_index=0, tensor_index=0
                    )

        # Wire up Node to Operations.
        self.operation._inbound_nodes.append(self)
        for kt in self.arguments.keras_tensors:
            inbound_op = kt._keras_history.operation
            if inbound_op is not None:  # It's a graph entry point.
                inbound_op._outbound_nodes.append(self)

        # Set metadata on outputs.
        if not zero_history:
            node_index = len(self.operation._inbound_nodes) - 1
            for i, tensor in enumerate(self.outputs):
                tensor._keras_history = KerasHistory(
                    operation=operation, node_index=node_index, tensor_index=i
                )

        # Whether this is a root node.
        self.is_input = not self.arguments.keras_tensors