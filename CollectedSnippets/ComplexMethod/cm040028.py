def build(self, input_shape):
        if input_shape is None:
            return

        ndim = len(input_shape)
        self._build_input_shape = input_shape

        if any(a < -ndim or a >= ndim for a in self.axis):
            raise ValueError(
                "All `axis` values must be in the range [-ndim, ndim). "
                f"Received inputs with ndim={ndim}, while axis={self.axis}"
            )

        # Axes to be kept, replacing negative values with positive equivalents.
        # Sorted to avoid transposing axes.
        self._keep_axis = tuple(
            sorted([d if d >= 0 else d + ndim for d in self.axis])
        )
        # All axes to be kept should have known shape.
        for d in self._keep_axis:
            if input_shape[d] is None:
                raise ValueError(
                    "All `axis` values to be kept must have a known shape. "
                    f"Received axis={self.axis}, "
                    f"inputs.shape={input_shape}, "
                    f"with unknown axis at index {d}"
                )
        # Axes to be reduced.
        self._reduce_axis = tuple(
            d for d in range(ndim) if d not in self._keep_axis
        )
        # 1 if an axis should be reduced, 0 otherwise.
        self._reduce_axis_mask = [
            0 if d in self._keep_axis else 1 for d in range(ndim)
        ]
        # Broadcast any reduced axes.
        self._broadcast_shape = [
            input_shape[d] if d in self._keep_axis else 1 for d in range(ndim)
        ]
        mean_and_var_shape = tuple(input_shape[d] for d in self._keep_axis)
        self._mean_and_var_shape = mean_and_var_shape

        if self.input_mean is None:
            self.adapt_mean = self.add_weight(
                name="mean",
                shape=mean_and_var_shape,
                initializer="zeros",
                trainable=False,
            )
            self.adapt_variance = self.add_weight(
                name="variance",
                shape=mean_and_var_shape,
                initializer="ones",
                trainable=False,
            )
            # For backwards compatibility with older saved models.
            self.count = self.add_weight(
                name="count",
                shape=(),
                dtype="int",
                initializer="zeros",
                trainable=False,
            )
            self.built = True
            self.finalize_state()

        else:
            mean = ops.convert_to_tensor(self.input_mean)
            variance = ops.convert_to_tensor(self.input_variance)

            if ops.ndim(mean) == 0:
                # Case 1: Scalar mean/variance
                mean = ops.broadcast_to(mean, self._broadcast_shape)
                variance = ops.broadcast_to(variance, self._broadcast_shape)
            else:
                # Case 2: General broadcasting. Align mean/variance dims
                # to the kept axes from right to left.
                expanded_shape = [1] * ndim
                mean_shape = ops.shape(mean)
                mean_ndim = ops.ndim(mean)

                # Map mean dimensions to the correct kept axes (right-to-left).
                # This handles cases where mean has fewer dims than keep_axis.
                for i in range(1, mean_ndim + 1):
                    axis_idx = self._keep_axis[-i]
                    expanded_shape[axis_idx] = mean_shape[-i]

                mean = ops.reshape(mean, expanded_shape)
                variance = ops.reshape(variance, expanded_shape)

                # Broadcast to the full target shape.
                mean = ops.broadcast_to(mean, self._broadcast_shape)
                variance = ops.broadcast_to(variance, self._broadcast_shape)

            self.mean = ops.cast(mean, dtype=self.compute_dtype)
            self.variance = ops.cast(variance, dtype=self.compute_dtype)
            self.built = True