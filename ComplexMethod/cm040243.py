def add(self, layer, rebuild=True):
        """Adds a layer instance on top of the layer stack.

        Args:
            layer: layer instance.
        """
        # Legacy case: if the first layer has an input_shape arg,
        # use it to build an InputLayer.
        if not self._layers:
            if getattr(layer, "_input_shape_arg", None) is not None:
                self.add(InputLayer(shape=layer._input_shape_arg))

        # If we are passed a Keras tensor created by keras.Input(), we
        # extract the input layer from its keras history and use that.
        if hasattr(layer, "_keras_history"):
            origin_layer = layer._keras_history[0]
            if isinstance(origin_layer, InputLayer):
                layer = origin_layer
        if not isinstance(layer, Layer):
            raise ValueError(
                "Only instances of `keras.Layer` can be "
                f"added to a Sequential model. Received: {layer} "
                f"(of type {type(layer)})"
            )
        if not self._is_layer_name_unique(layer):
            raise ValueError(
                "All layers added to a Sequential model "
                f"should have unique names. Name '{layer.name}' is already "
                "the name of a layer in this model. Update the `name` argument "
                "to pass a unique name."
            )
        if (
            isinstance(layer, InputLayer)
            and self._layers
            and isinstance(self._layers[0], InputLayer)
        ):
            raise ValueError(
                f"Sequential model '{self.name}' has already been configured "
                f"to use input shape {self._layers[0].batch_shape}. You cannot "
                f"add a different Input layer to it."
            )

        self._layers.append(layer)
        if rebuild:
            self._maybe_rebuild()
        else:
            self.built = False
            self._functional = None