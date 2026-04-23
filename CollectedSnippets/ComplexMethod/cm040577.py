def test_norm(self, ndim, ord, axis, keepdims):
        if ndim == 1:
            x = np.random.random((5,)).astype("float32")
        else:
            x = np.random.random((5, 6)).astype("float32")

        vector_norm = (ndim == 1) or isinstance(axis, int)

        axis_out_of_bounds = ndim == 1 and (
            axis == 1 or isinstance(axis, tuple)
        )
        expected_error = None
        # when an out of bounds axis triggers an IndexError on torch is complex
        if (
            axis_out_of_bounds
            and (not isinstance(axis, tuple) or ord is None)
            and ord not in ("fro", "nuc")
        ):
            expected_error = IndexError
        elif (
            axis_out_of_bounds
            or (vector_norm and isinstance(axis, tuple))  # inv. axis for vector
            or (vector_norm and ord in ("fro", "nuc"))  # invalid ord for vector
            or (not vector_norm and ord in (0, 3))  # invalid ord for matrix
        ):
            expected_error = RuntimeError

        if expected_error is not None:
            # Non-torch backends always throw a ValueError
            expected_error = (
                expected_error if backend.backend() == "torch" else ValueError
            )
            with self.assertRaises(expected_error):
                linalg.norm(x, ord=ord, axis=axis, keepdims=keepdims)
            return
        output = linalg.norm(x, ord=ord, axis=axis, keepdims=keepdims)
        expected_result = np.linalg.norm(
            x, ord=ord, axis=axis, keepdims=keepdims
        )
        self.assertAllClose(output, expected_result, atol=1e-5)