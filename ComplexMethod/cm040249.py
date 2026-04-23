def quantize(self, mode=None, config=None, filters=None, **kwargs):
        """Quantize the weights of the model.

        Note that the model must be built first before calling this method.
        `quantize` will recursively call `quantize(...)` in all layers and
        will be skipped if the layer doesn't implement the function.

        This method can be called by passing a `mode` string, which uses the
        default configuration for that mode. Alternatively, a `config` object
        can be passed to customize the behavior of the quantization (e.g. to
        use specific quantizers for weights or activations).

        Args:
            mode: The mode of the quantization. Supported modes are:
                `"int8"`, `"int4"`, `"float8"`, `"gptq"`. This is
                optional if `config` is provided.
            config: The configuration object specifying additional
                quantization options. This argument allows to configure
                the weight and activation quantizers. be an instance of
                `keras.quantizers.QuantizationConfig`.
            filters: Optional filters to apply to the quantization. Can be a
                regex string, a list of regex strings, or a callable. Only the
                layers which match the filter conditions will be quantized.
            **kwargs: Additional keyword arguments.

        Example:

        Quantize a model to int8 with default configuration:

        ```python
        # Build the model
        model = keras.Sequential([
            keras.Input(shape=(10,)),
            keras.layers.Dense(10),
        ])
        model.build((None, 10))

        # Quantize with default int8 config
        model.quantize("int8")
        ```

        Quantize a model to int8 with a custom configuration:

        ```python
        from keras.quantizers import Int8QuantizationConfig
        from keras.quantizers import AbsMaxQuantizer

        # Build the model
        model = keras.Sequential([
            keras.Input(shape=(10,)),
            keras.layers.Dense(10),
        ])
        model.build((None, 10))

        # Create a custom config
        config = Int8QuantizationConfig(
            weight_quantizer=AbsMaxQuantizer(
                axis=0,
                value_range=(-127, 127)
            ),
            activation_quantizer=AbsMaxQuantizer(
                axis=-1,
                value_range=(-127, 127)
            ),
        )

        # Quantize with custom config
        model.quantize(config=config)
        ```
        """
        # Validate inputs.
        type_check = kwargs.pop("type_check", True)
        if kwargs:
            raise ValueError(
                "Unrecognized keyword arguments "
                f"passed to {self.__class__.__name__}: {kwargs}"
            )

        if filters is not None:
            if not isinstance(filters, (str, Callable, list, tuple)):
                raise ValueError(
                    "The `filters` argument must be a regex string, a list of "
                    "regex strings, or a callable. Received: "
                    f"{type(filters)}"
                )

        graph_modified = False
        for layer in self._flatten_layers():
            # Apply filters
            if not should_quantize_layer(layer, filters):
                continue

            if len(list(layer._flatten_layers())) == 1:
                try:
                    layer.quantize(mode, type_check=type_check, config=config)
                    graph_modified = True
                except NotImplementedError as e:
                    warnings.warn(str(e))
                except AttributeError:
                    pass

        if mode in ["gptq", "awq"]:
            # Resolve model structure.
            # 1. If quantization_layer_structure is provided inside the config,
            # use that.
            structure = config.quantization_layer_structure
            # 2. If no layer structure is provided in the config, try to fetch
            # it using the `get_quantization_layer_structure` hook.
            if structure is None:
                structure = self.get_quantization_layer_structure(mode)

            if structure is None:
                raise ValueError(
                    f"For {mode=}, a valid quantization structure must be "
                    "provided either via `config.quantization_layer_structure` "
                    "or by overriding "
                    "`model.get_quantization_layer_structure(mode)`. The "
                    "structure should be a dictionary with keys "
                    "'pre_block_layers' and 'sequential_blocks'."
                )
            if mode == "gptq":
                gptq_quantize(config, structure, filters=filters)
            elif mode == "awq":
                awq_quantize(config, structure, filters=filters)

        # If any layer was changed, we must rebuild the execution functions.
        if graph_modified:
            self.train_function = None
            self.test_function = None
            self.predict_function = None
            self._post_quantize(mode, **kwargs)