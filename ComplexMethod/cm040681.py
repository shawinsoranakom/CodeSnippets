def convert_single_array(x):
        if x is None:
            return x

        # Special case: handle np "object" arrays containing strings
        if (
            isinstance(x, np.ndarray)
            and str(x.dtype) == "object"
            and backend.backend() == "tensorflow"
            and all(isinstance(e, str) for e in x)
        ):
            x = tf.convert_to_tensor(x, dtype="string")

        # Step 1. Determine which Sliceable class to use.
        if isinstance(x, np.ndarray):
            sliceable_class = NumpySliceable
        elif data_adapter_utils.is_tensorflow_tensor(x):
            if data_adapter_utils.is_tensorflow_ragged(x):
                sliceable_class = TensorflowRaggedSliceable
            elif data_adapter_utils.is_tensorflow_sparse(x):
                sliceable_class = TensorflowSparseSliceable
            else:
                sliceable_class = TensorflowSliceable
        elif data_adapter_utils.is_jax_array(x):
            if data_adapter_utils.is_jax_sparse(x):
                sliceable_class = JaxSparseSliceable
            else:
                x = np.asarray(x)
                sliceable_class = NumpySliceable
        elif data_adapter_utils.is_torch_tensor(x):
            sliceable_class = TorchSliceable
        elif pandas is not None and isinstance(x, pandas.DataFrame):
            sliceable_class = PandasDataFrameSliceable
        elif pandas is not None and isinstance(x, pandas.Series):
            sliceable_class = PandasSeriesSliceable
        elif data_adapter_utils.is_scipy_sparse(x):
            sliceable_class = ScipySparseSliceable
        elif hasattr(x, "__array__"):
            x = np.asarray(x)
            sliceable_class = NumpySliceable
        else:
            raise ValueError(
                "Expected a NumPy array, tf.Tensor, tf.RaggedTensor, "
                "tf.SparseTensor, jax.np.ndarray, "
                "jax.experimental.sparse.JAXSparse, torch.Tensor, "
                "Pandas Dataframe, or Pandas Series. Received invalid input: "
                f"{x} (of type {type(x)})"
            )

        # Step 2. Normalize floats to floatx.
        def is_non_floatx_float(dtype):
            return (
                dtype is not object
                and backend.is_float_dtype(dtype)
                and not backend.standardize_dtype(dtype) == backend.floatx()
            )

        cast_dtype = None
        if pandas is not None and isinstance(x, pandas.DataFrame):
            if any(is_non_floatx_float(d) for d in x.dtypes.values):
                cast_dtype = backend.floatx()
        else:
            if is_non_floatx_float(x.dtype):
                cast_dtype = backend.floatx()

        if cast_dtype is not None:
            x = sliceable_class.cast(x, cast_dtype)

        # Step 3. Apply target backend specific logic and optimizations.
        if target_backend is None:
            return sliceable_class(x)

        if target_backend == "tensorflow":
            return sliceable_class.convert_to_tf_dataset_compatible(x)

        # With dense arrays and JAX as output, it is faster to use NumPy as an
        # intermediary representation, so wrap input array in a NumPy array,
        # which should not use extra memory.
        # See https://github.com/google/jax/issues/1276 for an explanation of
        # why slicing a NumPy array is faster than slicing a JAX array.
        if target_backend == "jax" and sliceable_class in (
            TensorflowSliceable,
            TorchSliceable,
        ):
            x = np.asarray(x)
            sliceable_class = NumpySliceable

        return sliceable_class(x)