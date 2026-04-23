def __init__(
        self,
        layer,
        merge_mode="concat",
        weights=None,
        backward_layer=None,
        **kwargs,
    ):
        if not isinstance(layer, Layer):
            raise ValueError(
                "Please initialize `Bidirectional` layer with a "
                f"`keras.layers.Layer` instance. Received: {layer}"
            )
        if backward_layer is not None and not isinstance(backward_layer, Layer):
            raise ValueError(
                "`backward_layer` need to be a `keras.layers.Layer` "
                f"instance. Received: {backward_layer}"
            )
        if merge_mode not in ["sum", "mul", "ave", "concat", None]:
            raise ValueError(
                f"Invalid merge mode. Received: {merge_mode}. "
                "Merge mode should be one of "
                '{"sum", "mul", "ave", "concat", None}'
            )
        super().__init__(**kwargs)

        # Recreate the forward layer from the original layer config, so that it
        # will not carry over any state from the layer.
        config = serialization_lib.serialize_keras_object(layer)
        config["config"]["name"] = (
            f"forward_{utils.removeprefix(layer.name, 'forward_')}"
        )
        self.forward_layer = serialization_lib.deserialize_keras_object(config)

        if backward_layer is None:
            config = serialization_lib.serialize_keras_object(layer)
            config["config"]["go_backwards"] = True
            config["config"]["name"] = (
                f"backward_{utils.removeprefix(layer.name, 'backward_')}"
            )
            self.backward_layer = serialization_lib.deserialize_keras_object(
                config
            )
        else:
            self.backward_layer = backward_layer
        # Keep the use_cudnn attribute if defined (not serialized).
        if hasattr(layer, "use_cudnn"):
            self.forward_layer.use_cudnn = layer.use_cudnn
            self.backward_layer.use_cudnn = layer.use_cudnn
        self._verify_layer_config()

        def force_zero_output_for_mask(layer):
            # Force the zero_output_for_mask to be True if returning sequences.
            if getattr(layer, "zero_output_for_mask", None) is not None:
                layer.zero_output_for_mask = layer.return_sequences

        force_zero_output_for_mask(self.forward_layer)
        force_zero_output_for_mask(self.backward_layer)

        self.merge_mode = merge_mode
        if weights:
            nw = len(weights)
            self.forward_layer.initial_weights = weights[: nw // 2]
            self.backward_layer.initial_weights = weights[nw // 2 :]
        self.stateful = layer.stateful
        self.return_sequences = layer.return_sequences
        self.return_state = layer.return_state
        self.supports_masking = True
        self.input_spec = layer.input_spec