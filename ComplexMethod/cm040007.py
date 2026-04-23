def rematerialized_call(self, layer_call, *args, **kwargs):
        """Enable rematerialization dynamically for layer's call method.

        Args:
            layer_call: The original `call` method of a layer.

        Returns:
            Rematerialized layer's `call` method.
        """

        def compute_size(x):
            return (
                math.prod([d or 1 for d in x.shape])
                if isinstance(x, KerasTensor)
                else 0
            )

        # Full rematerialization
        if self._remat_mode.mode == "full":
            return remat.remat(layer_call)

        # Apply rematerialization to specific layers
        elif self._remat_mode.mode == "list_of_layers" and (
            self.name in self._remat_mode.layer_names
        ):
            return remat.remat(layer_call)

        # Apply rematerialization based on output size threshold
        elif self._remat_mode.mode == "larger_than":
            output_spec = self.compute_output_spec(*args, **kwargs)
            output_size = sum(
                tree.flatten(tree.map_structure(compute_size, output_spec))
            )
            if (
                output_size
                and output_size > self._remat_mode.output_size_threshold
            ):
                return remat.remat(layer_call)
        elif self._remat_mode.mode == "activations":
            has_activation = (
                hasattr(self, "activation") and self.activation is not None
            )
            if has_activation:

                @functools.wraps(layer_call)
                def rematerialized_activation_call_wrapper(*args, **kwargs):
                    original_activation = self.activation
                    self.activation = remat.remat(original_activation)
                    try:
                        return layer_call(*args, **kwargs)
                    finally:
                        self.activation = original_activation

                return rematerialized_activation_call_wrapper
        return layer_call