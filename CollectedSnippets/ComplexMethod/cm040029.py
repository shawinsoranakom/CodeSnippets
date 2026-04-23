def adapt(self, data):
        """Computes the mean and variance of values in a dataset.

        Calling `adapt()` on a `Normalization` layer is an alternative to
        passing in `mean` and `variance` arguments during layer construction. A
        `Normalization` layer should always either be adapted over a dataset or
        passed `mean` and `variance`.

        During `adapt()`, the layer will compute a `mean` and `variance`
        separately for each position in each axis specified by the `axis`
        argument. To calculate a single `mean` and `variance` over the input
        data, simply pass `axis=None` to the layer.

        Arg:
            data: The data to train on. It can be passed as a NumPy array, a
                backend-native eager tensor, a `tf.data.Dataset`, a
                `keras.utils.PyDataset`, or an iterable of batches (e.g. a
                list of arrays or a generator yielding batches). If a dataset
                or iterable, *it must be batched*. Keras will assume that each
                element is a batch, and if that assumption doesn't hold, the
                mean and variance may be incorrectly computed.
        """
        data_is_iterable = False
        if isinstance(data, np.ndarray) or backend.is_tensor(data):
            input_shape = data.shape
        elif isinstance(data, tf.data.Dataset):

            def get_input_shape(d):
                element_spec = d.element_spec
                x_spec = (
                    element_spec[0]
                    if isinstance(element_spec, tuple)
                    else element_spec
                )
                return tuple(x_spec.shape)

            input_shape = get_input_shape(data)
            if len(input_shape) == 1:
                data = data.batch(128)
                input_shape = get_input_shape(data)
        elif isinstance(data, PyDataset):
            input_shape = _extract_batch(data[0]).shape
        elif hasattr(data, "__iter__"):
            data_is_iterable = True
            # Consume first batch to infer input_shape; then chain it back for
            # accumulation so we iterate over (first_batch, *rest).
            data_iter = iter(data)
            first_batch = next(data_iter, None)
            if first_batch is None:
                raise ValueError(
                    "adapt() received an empty iterable (no batches). "
                    "Expected at least one batch. Pass a non-empty iterable "
                    "of arrays or tensors, e.g. layer.adapt([x]) or "
                    "layer.adapt(list_of_batches)."
                )
            first_batch = _extract_batch(first_batch)
            input_shape = getattr(first_batch, "shape", None)
            if input_shape is None:
                raise TypeError(
                    "adapt() expects an iterable that yields arrays or "
                    "tensors with a `.shape` attribute (e.g. numpy arrays or "
                    "backend tensors). Got an element of type "
                    f"{type(first_batch).__name__}. Ensure each yielded "
                    "element is array-like with a `.shape` attribute."
                )
            input_shape = tuple(input_shape)
            data = itertools.chain([first_batch], data_iter)
        else:
            raise TypeError(
                f"Unsupported data type: {type(data)}. `adapt` supports "
                f"`np.ndarray`, backend tensors, `tf.data.Dataset`, "
                f"`keras.utils.PyDataset`, and iterables of batches (e.g. "
                f"list, generator)."
            )

        if not self.built:
            self.build(input_shape)
        else:
            for d in self._keep_axis:
                if input_shape[d] != self._build_input_shape[d]:
                    raise ValueError(
                        "The layer was built with "
                        f"input_shape={self._build_input_shape}, "
                        "but adapt() is being called with data with "
                        f"an incompatible shape, data.shape={input_shape}"
                    )

        if isinstance(data, np.ndarray):
            total_mean = np.mean(data, axis=self._reduce_axis)
            total_var = np.var(data, axis=self._reduce_axis)
        elif backend.is_tensor(data):
            total_mean = ops.mean(data, axis=self._reduce_axis)
            total_var = ops.var(data, axis=self._reduce_axis)
        elif isinstance(data, (tf.data.Dataset, PyDataset)) or data_is_iterable:
            total_mean = ops.zeros(self._mean_and_var_shape)
            total_var = ops.zeros(self._mean_and_var_shape)
            total_count = 0
            for batch in data:
                batch = _extract_batch(batch)
                batch = backend.convert_to_tensor(
                    batch, dtype=self.compute_dtype
                )
                for d in self._keep_axis:
                    batch_dim = batch.shape[d]
                    expected = self._build_input_shape[d]
                    if (
                        batch_dim is not None
                        and expected is not None
                        and batch_dim != expected
                    ):
                        raise ValueError(
                            "adapt() yielded a batch with incompatible "
                            "shape. Expected "
                            f"{self._build_input_shape}, got "
                            f"{tuple(batch.shape)}."
                        )
                batch_mean = ops.mean(batch, axis=self._reduce_axis)
                batch_var = ops.var(batch, axis=self._reduce_axis)
                if self._reduce_axis:
                    batch_reduce_shape = (
                        batch.shape[d] for d in self._reduce_axis
                    )
                    batch_count = math.prod(batch_reduce_shape)
                else:
                    batch_count = 1

                total_count += batch_count
                batch_weight = float(batch_count) / total_count
                existing_weight = 1.0 - batch_weight
                new_total_mean = (
                    total_mean * existing_weight + batch_mean * batch_weight
                )
                # The variance is computed using the lack-of-fit sum of squares
                # formula (see
                # https://en.wikipedia.org/wiki/Lack-of-fit_sum_of_squares).
                total_var = (
                    total_var + (total_mean - new_total_mean) ** 2
                ) * existing_weight + (
                    batch_var + (batch_mean - new_total_mean) ** 2
                ) * batch_weight
                total_mean = new_total_mean
        else:
            raise NotImplementedError(f"Unsupported data type: {type(data)}")

        self.adapt_mean.assign(total_mean)
        self.adapt_variance.assign(total_var)
        self.finalize_state()