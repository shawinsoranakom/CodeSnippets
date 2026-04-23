def __init__(self, inputs, outputs, name=None, **kwargs):
        if isinstance(inputs, dict):
            for k, v in inputs.items():
                if isinstance(v, backend.KerasTensor) and k != v.name:
                    warnings.warn(
                        "When providing `inputs` as a dict, all keys in the "
                        "dict must match the names of the corresponding "
                        f"tensors. Received key '{k}' mapping to value {v} "
                        f"which has name '{v.name}'. Change the tensor name to "
                        f"'{k}' (via `Input(..., name='{k}')`)"
                    )

        trainable = kwargs.pop("trainable", None)
        flat_inputs = tree.flatten(inputs)
        flat_outputs = tree.flatten(outputs)
        for x in flat_inputs:
            if not isinstance(x, backend.KerasTensor):
                raise ValueError(
                    "All `inputs` values must be KerasTensors. Received: "
                    f"inputs={inputs} including invalid value {x} of "
                    f"type {type(x)}"
                )
        for x in flat_outputs:
            if not isinstance(x, backend.KerasTensor):
                raise ValueError(
                    "All `outputs` values must be KerasTensors. Received: "
                    f"outputs={outputs} including invalid value {x} of "
                    f"type {type(x)}"
                )

        if not all(is_input_keras_tensor(t) for t in flat_inputs):
            inputs, outputs = clone_graph_nodes(inputs, outputs)

        Function.__init__(self, inputs, outputs, name=name)

        if trainable is not None:
            self.trainable = trainable

        self._layers = self.layers
        self.build(None)
        # We will convert directly (to the correct dtype per input).
        self._convert_input_args = False
        self._allow_non_tensor_positional_args = True
        output_layers = [x._keras_history[0] for x in self.outputs]
        self.output_names = [x.name for x in output_layers]