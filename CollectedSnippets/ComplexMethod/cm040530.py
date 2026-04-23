def compute_output_spec(self, inputs, start_indices):
        if len(self.shape) != len(inputs.shape):
            raise ValueError(
                "The number of dimensions in `inputs` must match the number of "
                f"dimensions in `shape`. Received inputs.shape={inputs.shape} "
                f"and shape={self.shape}"
            )
        if hasattr(start_indices, "__len__") and len(start_indices) != len(
            inputs.shape
        ):
            raise ValueError(
                "The number of dimensions in `start_indices` must match the "
                "number of dimensions in `inputs`. Received "
                f"start_indices={start_indices} and inputs.shape={inputs.shape}"
            )

        final_shape = []
        for i, (input_dim, slice_dim) in enumerate(
            zip(inputs.shape, self.shape)
        ):
            if slice_dim != -1:
                final_shape.append(slice_dim)
            elif isinstance(start_indices, KerasTensor) or input_dim is None:
                final_shape.append(None)
            else:
                final_shape.append(input_dim - start_indices[i])
        return KerasTensor(final_shape, dtype=inputs.dtype)