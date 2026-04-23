def test_standardize_dtype(self, dtype):
        """Tests standardize_dtype for all ALLOWED_DTYPES except string."""
        if backend.backend() == "torch" and dtype in (
            "uint16",
            "uint32",
            "uint64",
            "complex64",
            "complex128",
        ):
            self.skipTest(f"torch backend does not support dtype {dtype}")

        if backend.backend() == "jax":
            if dtype in ("complex128",):
                self.skipTest(f"jax backend does not support dtype {dtype}")
            import jax

            if not jax.config.x64_enabled and "64" in dtype:
                self.skipTest(
                    f"jax backend does not support {dtype} without x64 enabled"
                )

        if backend.backend() == "openvino" and dtype in (
            "complex64",
            "complex128",
        ):
            self.skipTest(f"openvino backend does not support dtype {dtype}")

        x = backend.convert_to_tensor(np.zeros(()), dtype)
        actual = standardize_dtype(x.dtype)
        self.assertEqual(actual, dtype)