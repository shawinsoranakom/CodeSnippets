def assertEqualHelper(
        self, actual, expected, msg, *, dtype, exact_dtype=True, **kwargs
    ):
        if not isinstance(actual, torch.Tensor):
            raise AssertionError(
                f"expected actual to be torch.Tensor, got {type(actual)}"
            )

        # Some NumPy functions return scalars, not arrays
        if isinstance(expected, Number):
            self.assertEqual(actual.item(), expected, msg=msg, **kwargs)
        elif isinstance(expected, np.ndarray):
            # Handles exact dtype comparisons between arrays and tensors
            if exact_dtype:
                # Allows array dtype to be float32 when comparing with bfloat16 tensors
                #   since NumPy doesn't support the bfloat16 dtype
                # Also ops like scipy.special.erf, scipy.special.erfc, etc, promote float16
                # to float32
                if expected.dtype == np.float32:
                    if actual.dtype not in (
                        torch.float16,
                        torch.bfloat16,
                        torch.float32,
                    ):
                        raise AssertionError(
                            f"actual.dtype {actual.dtype} not in expected dtypes"
                        )
                else:
                    if expected.dtype != torch_to_numpy_dtype_dict[actual.dtype]:
                        raise AssertionError(
                            f"dtype mismatch: {expected.dtype} != {torch_to_numpy_dtype_dict[actual.dtype]}"
                        )

            self.assertEqual(
                actual,
                torch.from_numpy(expected).to(actual.dtype),
                msg,
                exact_device=False,
                **kwargs,
            )
        else:
            self.assertEqual(actual, expected, msg, exact_device=False, **kwargs)