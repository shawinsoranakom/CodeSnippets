def test_numpy_ref(self, device, dtype, op):
        if (
            TEST_WITH_TORCHINDUCTOR
            and op.formatted_name
            in ("signal_windows_exponential", "signal_windows_bartlett")
            and dtype == torch.float64
            and ("cuda" in device or "xpu" in device)
            or "cpu" in device
        ):
            raise unittest.SkipTest("XXX: raises tensor-likes are not close.")

        # Sets the default dtype to NumPy's default dtype of double
        with set_default_dtype(highest_precision_float(device)):
            for sample_input in op.reference_inputs(device, dtype):
                self.compare_with_reference(
                    op, op.ref, sample_input, exact_dtype=(dtype is not torch.long)
                )