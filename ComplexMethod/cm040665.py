def compute_loss(
        self,
        x=None,
        y=None,
        y_pred=None,
        sample_weight=None,
        training=True,
    ):
        """Compute the total loss, validate it, and return it.

        Subclasses can optionally override this method to provide custom loss
        computation logic.

        Example:

        ```python
        class MyModel(Model):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.loss_tracker = metrics.Mean(name='loss')

            def compute_loss(self, x, y, y_pred, sample_weight, training=True):
                loss = ops.mean((y_pred - y) ** 2)
                loss += ops.sum(self.losses)
                self.loss_tracker.update_state(loss)
                return loss

            def reset_metrics(self):
                self.loss_tracker.reset_state()

            @property
            def metrics(self):
                return [self.loss_tracker]

        inputs = layers.Input(shape=(10,), name='my_input')
        outputs = layers.Dense(10)(inputs)
        model = MyModel(inputs, outputs)
        model.add_loss(ops.sum(outputs))

        optimizer = SGD()
        model.compile(optimizer, loss='mse', steps_per_execution=10)
        dataset = ...
        model.fit(dataset, epochs=2, steps_per_epoch=10)
        print(f"Custom loss: {model.loss_tracker.result()}")
        ```

        Args:
            x: Input data.
            y: Target data.
            y_pred: Predictions returned by the model (output of `model(x)`)
            sample_weight: Sample weights for weighting the loss function.
            training: Whether we are training or evaluating the model.

        Returns:
            The total loss as a scalar tensor, or `None` if no loss results
            (which is the case when called by `Model.test_step`).
        """
        # The default implementation does not use `x` or `training`.
        del x
        del training
        losses = []
        if self._compile_loss is not None:
            loss = self._compile_loss(y, y_pred, sample_weight)
            if loss is not None:
                losses.append(loss)
        for loss in self.losses:
            losses.append(self._aggregate_additional_loss(loss))
        if backend.backend() != "jax" and len(losses) == 0:
            raise ValueError(
                "No loss to compute. Provide a `loss` argument in `compile()`."
            )
        if len(losses) == 1:
            total_loss = losses[0]
        elif len(losses) == 0:
            total_loss = ops.zeros(())
        else:
            total_loss = ops.sum(losses)
        return total_loss