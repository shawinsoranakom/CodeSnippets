def call(self, inputs, training=None, mask=None):
        # Check if the mask has one less dimension than the inputs.
        if mask is not None:
            if len(mask.shape) != len(inputs.shape) - 1:
                # Raise a value error
                raise ValueError(
                    "The mask provided should be one dimension less "
                    "than the inputs. Received: "
                    f"mask.shape={mask.shape}, inputs.shape={inputs.shape}"
                )

        compute_dtype = backend.result_type(inputs.dtype, "float32")
        # BN is prone to overflow with float16/bfloat16 inputs, so we upcast to
        # float32 for the subsequent computations.
        inputs = ops.cast(inputs, compute_dtype)

        moving_mean = ops.cast(self.moving_mean, inputs.dtype)
        moving_variance = ops.cast(self.moving_variance, inputs.dtype)

        if self.scale:
            gamma = ops.cast(self.gamma, inputs.dtype)
        else:
            gamma = None

        if self.center:
            beta = ops.cast(self.beta, inputs.dtype)
        else:
            beta = None

        if training and self.trainable:
            mean, variance = self._moments(inputs, mask)

            if self.renorm:
                # Compute renorm corrections (r and d).
                (
                    r,
                    d,
                    mean,
                    variance,
                ) = self._renorm_correction_and_moments(mean, variance)

                # x = x * gamma + beta without renorm, and
                # (x * r + d) * gamma + beta = x * (r * gamma) + (d * gamma +
                # beta) with renorm.
                gamma, beta = self._compose_transforms(
                    r, d, gamma, beta, inputs.dtype
                )

                # Update moving statistics.
                self._update_renorm_statistics(mean, variance)
            else:
                self.moving_mean.assign(
                    moving_mean * self.momentum + mean * (1.0 - self.momentum)
                )
                self.moving_variance.assign(
                    moving_variance * self.momentum
                    + variance * (1.0 - self.momentum)
                )
        else:
            mean = moving_mean
            variance = moving_variance

        outputs = ops.batch_normalization(
            x=inputs,
            mean=mean,
            variance=variance,
            axis=self.axis,
            offset=beta,
            scale=gamma,
            epsilon=self.epsilon,
        )
        return ops.cast(outputs, self.compute_dtype)