def __init__(self, layer, config=GPTQConfig(tokenizer=None, dataset=None)):
        self.original_layer = layer
        self.num_samples = 0
        self.config = config
        self.quantizer = GPTQQuantizer(
            config, compute_dtype=layer.variable_dtype
        )

        # Explicitly handle each supported layer type
        if isinstance(layer, Dense) or (
            isinstance(layer, EinsumDense) and layer.kernel.ndim == 2
        ):
            # For a standard Dense layer, the dimensions are straightforward.
            self.kernel_shape = layer.kernel.shape
            # rows: [input_features]
            self.rows = self.kernel_shape[0]
            # columns: [output_features]
            self.columns = self.kernel_shape[1]
            self.layer = layer

        # Handle 3D EinsumDense layers (typically from attention blocks).
        elif isinstance(layer, EinsumDense) and layer.kernel.ndim == 3:
            # For EinsumDense, we determine the effective 2D dimensions.
            self.kernel_shape = layer.kernel.shape
            shape = list(self.kernel_shape)
            d_model_dim_index = shape.index(max(shape))

            if d_model_dim_index == 0:  # QKV projection case
                in_features, heads, head_dim = shape
                self.rows, self.columns = (
                    in_features,
                    ops.multiply(heads, head_dim),
                )
            elif d_model_dim_index in [1, 2]:  # Attention Output case
                heads, head_dim, out_features = shape
                self.rows, self.columns = (
                    ops.multiply(heads, head_dim),
                    out_features,
                )

            # Create a temporary object that holds a reshaped
            # 2D version of the kernel.
            self.layer = types.SimpleNamespace(
                kernel=ops.reshape(layer.kernel, (self.rows, self.columns)),
            )
        else:
            # Raise an error if the layer is not supported.
            raise TypeError(f"Unsupported layer type for GPTQ: {type(layer)}")
        self.hessian = ops.zeros((self.rows, self.rows), dtype="float32")