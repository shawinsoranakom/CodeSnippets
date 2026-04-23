def call(self, inputs, training=None, mask=None):
        # Validate mask shape using static shape info when available
        if mask is not None:
            mask_shape = mask.shape
            input_shape = inputs.shape

            # Check if mask has at least 2 dimensions (batch and timesteps)
            if len(mask_shape) < 2:
                raise ValueError(
                    "The `mask` passed to the `TimeDistributed` layer must be "
                    "at least 2D (e.g., `(batch_size, timesteps)`), but it has "
                    f"{len(mask_shape)} dimension(s) with shape {mask_shape}."
                )

            # Check batch size and timesteps dimensions match
            batch_mismatch = (
                input_shape[0] is not None
                and mask_shape[0] is not None
                and input_shape[0] != mask_shape[0]
            )
            time_mismatch = (
                input_shape[1] is not None
                and mask_shape[1] is not None
                and input_shape[1] != mask_shape[1]
            )

            if batch_mismatch or time_mismatch:
                raise ValueError(
                    "The `mask` passed to the `TimeDistributed` layer has a "
                    f"shape {mask_shape} that is incompatible with the input "
                    f"shape {input_shape}. The first two dimensions of the "
                    "mask (batch size and timesteps) must match the input's "
                    "first two dimensions. Expected mask shape prefix: "
                    f"({input_shape[0]}, {input_shape[1]})."
                )

        input_shape = ops.shape(inputs)

        def time_distributed_transpose(data):
            """Swaps the timestep and batch dimensions of a tensor."""
            axes = [1, 0, *range(2, len(data.shape))]
            return ops.transpose(data, axes=axes)

        inputs = time_distributed_transpose(inputs)
        if mask is not None:
            mask = time_distributed_transpose(mask)

        def step_function(i):
            kwargs = {}
            if self.layer._call_has_mask_arg and mask is not None:
                kwargs["mask"] = mask[i]
            if self.layer._call_has_training_arg:
                kwargs["training"] = training
            return self.layer.call(inputs[i], **kwargs)

        # Implementation #1: is the time axis is static, use a Python for loop.

        if inputs.shape[0] is not None:
            outputs = ops.stack(
                [step_function(i) for i in range(inputs.shape[0])]
            )
            return time_distributed_transpose(outputs)

        # Implementation #2: use backend.vectorized_map.

        outputs = backend.vectorized_map(
            step_function, ops.arange(input_shape[0])
        )
        return time_distributed_transpose(outputs)