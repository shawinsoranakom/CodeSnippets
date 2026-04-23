def adapt(self, data, steps=None):
        """Computes bin boundaries from quantiles in a input dataset.

        Calling `adapt()` on a `Discretization` layer is an alternative to
        passing in a `bin_boundaries` argument during construction. A
        `Discretization` layer should always be either adapted over a dataset or
        passed `bin_boundaries`.

        During `adapt()`, the layer will estimate the quantile boundaries of the
        input dataset. The number of quantiles can be controlled via the
        `num_bins` argument, and the error tolerance for quantile boundaries can
        be controlled via the `epsilon` argument.

        Arguments:
            data: The data to train on. It can be passed either as a
                batched `tf.data.Dataset`, a Grain dataset, as a NumPy
                array, or as any iterable of batches (e.g. a list of
                arrays or a generator yielding batches).
            steps: Integer or `None`.
                Total number of steps (batches of samples) to process.
                If `data` is a `tf.data.Dataset`, and `steps` is `None`,
                `adapt()` will run until the input dataset is exhausted.
                When passing an infinitely
                repeating dataset, you must specify the `steps` argument. This
                argument is not supported with array inputs or list inputs.
        """
        if self.num_bins is None:
            raise ValueError(
                "Cannot adapt a Discretization layer that has been initialized "
                "with `bin_boundaries`, use `num_bins` instead."
            )
        self.reset_state()
        if isinstance(data, tf.data.Dataset):
            if steps is not None:
                data = data.take(steps)
            for batch in data:
                self.update_state(batch)
        elif hasattr(data, "__iter__") and not (
            isinstance(data, np.ndarray)
            or backend.is_tensor(data)
            or tf.is_tensor(data)
        ):
            for i, batch in enumerate(data):
                if steps is not None and i >= steps:
                    break
                self.update_state(batch)
        else:
            self.update_state(data)
        self.finalize_state()