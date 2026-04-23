def update_state(self, y_true, y_pred, sample_weight=None):
        """Accumulates the confusion matrix statistics.

        Args:
            y_true: The ground truth values.
            y_pred: The predicted values.
            sample_weight: Optional weighting of each example. Can
                be a `Tensor` whose rank is either 0, or the same as `y_true`,
                and must be broadcastable to `y_true`. Defaults to `1`.

        Returns:
            Update op.
        """

        if not self.sparse_y_true:
            y_true = ops.argmax(y_true, axis=self.axis)
        if not self.sparse_y_pred:
            y_pred = ops.argmax(y_pred, axis=self.axis)

        y_true = ops.convert_to_tensor(y_true, dtype=self.dtype)
        y_pred = ops.convert_to_tensor(y_pred, dtype=self.dtype)

        # Flatten the input if its rank > 1.
        if len(y_pred.shape) > 1:
            y_pred = ops.reshape(y_pred, [-1])

        if len(y_true.shape) > 1:
            y_true = ops.reshape(y_true, [-1])

        if sample_weight is None:
            sample_weight = 1
        else:
            if (
                hasattr(sample_weight, "dtype")
                and "float" in str(sample_weight.dtype)
                and "int" in str(self.dtype)
            ):
                warnings.warn(
                    "You are passing weight as `float`, but dtype is `int`. "
                    "This may result in an incorrect weight due to type casting"
                    " Consider using integer weights."
                )
        sample_weight = ops.convert_to_tensor(sample_weight, dtype=self.dtype)

        if len(sample_weight.shape) > 1:
            sample_weight = ops.reshape(sample_weight, [-1])

        sample_weight = ops.broadcast_to(sample_weight, ops.shape(y_true))

        if self.ignore_class is not None:
            ignore_class = ops.convert_to_tensor(
                self.ignore_class, y_true.dtype
            )
            valid_mask = ops.not_equal(y_true, ignore_class)
            y_true = y_true * ops.cast(valid_mask, y_true.dtype)
            y_pred = y_pred * ops.cast(valid_mask, y_pred.dtype)
            if sample_weight is not None:
                sample_weight = sample_weight * ops.cast(
                    valid_mask, sample_weight.dtype
                )

        y_pred = ops.cast(y_pred, dtype=self.dtype)
        y_true = ops.cast(y_true, dtype=self.dtype)
        sample_weight = ops.cast(sample_weight, dtype=self.dtype)

        current_cm = confusion_matrix(
            y_true,
            y_pred,
            self.num_classes,
            weights=sample_weight,
            dtype=self.dtype,
        )

        return self.total_cm.assign(self.total_cm + current_cm)