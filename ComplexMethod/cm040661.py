def convert_input(self, x, autocast, dtype):
        """Converts the input dtype based on `autocast` and `dtype`.

        Note that `x` can be a tensor, symbolic tensor or numpy array, and this
        method will keep integer inputs untouched and only apply casting to
        floats.
        """

        dtype = backend.standardize_dtype(dtype)
        if backend.is_tensor(x):
            if self._should_cast(x, autocast, dtype):
                x = backend.cast(x, dtype=dtype)
            return x
        elif backend.is_keras_tensor(x):
            if self._should_cast(x, autocast, dtype):
                x = ops.cast(x, dtype=dtype)
            return x
        elif hasattr(x, "__array__"):
            try:
                x = backend.convert_to_tensor(x)
            except TypeError:
                x = backend.convert_to_tensor(x, dtype=dtype)
            if self._should_cast(x, autocast, dtype):
                x = backend.cast(x, dtype=dtype)
            return x
        return x