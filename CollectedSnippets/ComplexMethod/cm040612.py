def __init__(self, layer, config=None):
        from keras.src.quantizers.awq_config import AWQConfig

        self.original_layer = layer
        self.config = config or AWQConfig(dataset=None, tokenizer=None)
        self.num_samples = 0

        # Handle Dense and EinsumDense layers
        if isinstance(layer, Dense) or (
            isinstance(layer, EinsumDense) and layer.kernel.ndim == 2
        ):
            self.kernel_shape = layer.kernel.shape
            self.rows = self.kernel_shape[0]  # in_features
            self.columns = self.kernel_shape[1]  # out_features
            self.layer = layer
        elif isinstance(layer, EinsumDense) and layer.kernel.ndim == 3:
            # Handle 3D EinsumDense layers (typically from attention blocks)
            self.kernel_shape = layer.kernel.shape
            shape = list(self.kernel_shape)
            d_model_dim_index = shape.index(max(shape))

            if d_model_dim_index == 0:  # QKV projection case
                in_features, heads, head_dim = shape
                self.rows = in_features
                self.columns = heads * head_dim
            elif d_model_dim_index in [1, 2]:  # Attention Output case
                heads, head_dim, out_features = shape
                self.rows = heads * head_dim
                self.columns = out_features
            else:
                raise ValueError(
                    f"Cannot determine dimensions for EinsumDense kernel "
                    f"shape {shape}"
                )

            # Create a temporary object that holds a reshaped 2D version
            self.layer = types.SimpleNamespace(
                kernel=ops.reshape(layer.kernel, (self.rows, self.columns)),
            )
        else:
            raise TypeError(f"Unsupported layer type for AWQ: {type(layer)}")

        # Initialize activation magnitude accumulator (per-channel max)
        self.activation_magnitudes = ops.zeros((self.rows,), dtype="float32")