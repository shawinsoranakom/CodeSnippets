def update_hessian_with_batch(self, input_batch):
        """
        Updates the running average of the Hessian matrix with a new batch.

        This method computes the Hessian matrix for a given batch of input
        activations and updates the accumulated Hessian (`self.hessian`) using a
        numerically stable running average. This allows the Hessian to be
        computed over a large dataset without loading all samples into memory
        at once.

        The input tensor is first reshaped into a 2D matrix [num_samples,
        num_features] before the Hessian is calculated.

        Args:
            input_batch: A 2D or higher-dimensional tensor of input activations
                from a calibration batch.

        Raises:
            ValueError: If the feature dimension of the input tensor
                `input_batch` does not match the dimensions of the
                pre-initialized Hessian matrix `self.hessian`.
        """
        if input_batch is None:
            raise ValueError("Input tensor cannot be None.")

        if len(input_batch.shape) < 2:
            raise ValueError(
                "Input tensor must have rank >= 2 "
                f"(got rank {len(input_batch.shape)})."
            )
        if ops.size(input_batch) == 0:
            raise ValueError("Input tensor cannot be empty.")
        if len(input_batch.shape) > 2:
            # [batch, features]
            input_batch = ops.reshape(input_batch, (-1, input_batch.shape[-1]))
        x = ops.cast(input_batch, "float32")

        num_new_samples = ops.shape(x)[0]
        num_prev_samples = self.num_samples
        total_samples = ops.add(num_prev_samples, num_new_samples)

        if ops.shape(self.hessian)[0] != ops.shape(x)[-1]:
            raise ValueError(
                f"Hessian dimensions ({ops.shape(self.hessian)[0]}) do not "
                f"match input features ({ops.shape(x)[-1]})."
            )

        # gram_matrix: [features, features]
        gram_matrix = ops.matmul(ops.transpose(x), x)
        # Ensures numerical stability and symmetry in case of large floating
        # point activations.
        gram_matrix = ops.divide(
            ops.add(gram_matrix, ops.transpose(gram_matrix)), 2.0
        )

        # Decay previous mean and add current per-sample contribution
        # (factor 2/N)
        if self.num_samples > 0:
            self.hessian = ops.multiply(
                self.hessian, ops.divide(num_prev_samples, total_samples)
            )

        self.hessian = ops.add(
            self.hessian,
            ops.multiply(ops.divide(2.0, total_samples), gram_matrix),
        )

        self.num_samples = self.num_samples + ops.shape(x)[0] or 0