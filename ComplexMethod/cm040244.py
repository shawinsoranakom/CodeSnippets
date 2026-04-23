def build(self, input_shape=None):
        try:
            input_shape = standardize_shape(input_shape)
        except:
            # Do not attempt to build if the model does not have a single
            # input tensor.
            return
        if not self._layers:
            raise ValueError(
                f"Sequential model {self.name} cannot be built because it has "
                "no layers. Call `model.add(layer)`."
            )
        if isinstance(self._layers[0], InputLayer):
            if self._layers[0].batch_shape != input_shape:
                raise ValueError(
                    f"Sequential model '{self.name}' has already been "
                    "configured to use input shape "
                    f"{self._layers[0].batch_shape}. You cannot build it "
                    f"with input_shape {input_shape}"
                )
        else:
            dtype = self._layers[0].compute_dtype
            self._layers = [
                InputLayer(batch_shape=input_shape, dtype=dtype)
            ] + self._layers

        # Build functional model
        inputs = self._layers[0].output
        x = inputs
        for layer in self._layers[1:]:
            try:
                x = layer(x)
            except NotImplementedError:
                # Can happen if shape inference is not implemented.
                # TODO: consider reverting inbound nodes on layers processed.
                return
            except TypeError as e:
                signature = inspect.signature(layer.call)
                positional_args = [
                    param
                    for param in signature.parameters.values()
                    if param.kind
                    in (
                        inspect.Parameter.POSITIONAL_ONLY,
                        inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    )
                ]
                required_positional_args = [
                    param
                    for param in positional_args
                    if param.default == inspect.Parameter.empty
                ]
                if not positional_args:
                    raise ValueError(
                        "Layers added to a Sequential model should "
                        "have a single positional argument, the "
                        "input tensor. Layer "
                        f"{layer.__class__.__name__} has no "
                        "positional arguments."
                    )
                if len(required_positional_args) > 1:
                    raise ValueError(
                        "Layers added to a Sequential model can "
                        "only have a single required positional "
                        "argument, the input tensor. Layer "
                        f"{layer.__class__.__name__} has multiple "
                        "required positional arguments: "
                        f"{required_positional_args}"
                    )
                raise e
        outputs = x
        self._functional = Functional(inputs=inputs, outputs=outputs)