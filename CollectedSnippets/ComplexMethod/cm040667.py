def _symbolic_build(self, iterator=None, data_batch=None):
        model_unbuilt = not all(layer.built for layer in self._flatten_layers())
        compile_metrics_unbuilt = (
            self._compile_metrics is not None
            and not self._compile_metrics.built
        )
        compile_loss_unbuilt = (
            self._compile_loss is not None and not self._compile_loss.built
        )
        optimizer_unbuilt = (
            self.optimizer is not None and not self.optimizer.built
        )
        if model_unbuilt or compile_metrics_unbuilt or compile_loss_unbuilt:
            # Create symbolic tensors matching an input batch.

            def to_symbolic_input(v):
                if v is None:
                    return None
                return backend.KerasTensor(
                    v.shape, backend.standardize_dtype(v.dtype)
                )

            if data_batch is None:
                for _, _, data_or_iterator in iterator:
                    if isinstance(data_or_iterator, (list, tuple)):
                        data_batch = data_or_iterator[0]
                    else:
                        data_batch = next(data_or_iterator)
                    break
            data_batch = tree.map_structure(to_symbolic_input, data_batch)
            (
                x,
                y,
                sample_weight,
            ) = data_adapter_utils.unpack_x_y_sample_weight(data_batch)

            # Build all model state with `backend.compute_output_spec`.
            try:
                y_pred = backend.compute_output_spec(self, x, training=False)
            except Exception as e:
                # If the underlying failure is a ValueError (e.g. invalid
                # inputs provided by the user), propagate it so callers
                # (and tests) can observe the original error type. For
                # other unexpected exceptions, raise a RuntimeError with
                # context to guide the user.
                if isinstance(e, ValueError):
                    raise
                raise RuntimeError(
                    "Unable to automatically build the model. "
                    "Please build it yourself before calling "
                    "fit/evaluate/predict. "
                    "A model is 'built' when its variables have "
                    "been created and its `self.built` attribute "
                    "is True. Usually, calling the model on a batch "
                    "of data is the right way to build it.\n"
                    "Exception encountered:\n"
                    f"'{e}'"
                )
            if compile_metrics_unbuilt:
                # Build all metric state with `backend.compute_output_spec`.
                backend.compute_output_spec(
                    self.compute_metrics,
                    x,
                    y,
                    y_pred,
                    sample_weight=sample_weight,
                )
            if compile_loss_unbuilt:
                # Build `CompileLoss` state with `backend.compute_output_spec`.
                backend.compute_output_spec(
                    self._compute_loss,
                    x,
                    y,
                    y_pred,
                    sample_weight=sample_weight,
                    training=False,
                )
        if optimizer_unbuilt:
            # Build optimizer
            self.optimizer.build(self.trainable_variables)
        self._post_build()