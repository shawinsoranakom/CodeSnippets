def _test_reference_numerics(self, dtype, op, gen, equal_nan=True):
        def _helper_reference_numerics(
            expected, actual, msg, exact_dtype, equal_nan=True
        ):
            if not torch.can_cast(
                numpy_to_torch_dtype_dict[expected.dtype.type], dtype
            ):
                exact_dtype = False

            if dtype is torch.bfloat16 and expected.dtype == np.float32:
                # Ref: https://github.com/pytorch/pytorch/blob/master/torch/testing/_internal/common_utils.py#L1149
                self.assertEqualHelper(
                    actual,
                    expected,
                    msg,
                    dtype=dtype,
                    exact_dtype=exact_dtype,
                    rtol=16e-3,
                    atol=1e-5,
                )
            else:
                self.assertEqualHelper(
                    actual,
                    expected,
                    msg,
                    dtype=dtype,
                    equal_nan=equal_nan,
                    exact_dtype=exact_dtype,
                )

        for sample in gen:
            # Each sample input acquired from the generator is just one lhs tensor
            #   and one rhs tensor
            l = sample.input
            r = sample.args[0]

            numpy_sample = sample.numpy()
            l_numpy = numpy_sample.input
            r_numpy = numpy_sample.args[0]
            actual = op(l, r)
            expected = op.ref(l_numpy, r_numpy)

            # Dtype promo rules have changed since NumPy 2.
            # Specialize the backward-incompatible cases.
            if (
                np.__version__ > "2"
                and op.name in ("sub", "_refs.sub")
                and isinstance(l_numpy, np.ndarray)
            ):
                expected = expected.astype(l_numpy.dtype)

            # Crafts a custom error message for smaller, printable tensors
            def _numel(x):
                if isinstance(x, torch.Tensor):
                    return x.numel()
                # Assumes x is a scalar
                return 1

            if _numel(l) <= 100 and _numel(r) <= 100:
                msg = (
                    "Failed to produce expected results! Input lhs tensor was"
                    f" {l}, rhs tensor was {r}, torch result is {actual}, and reference result is"
                    f" {expected}."
                )
            else:
                msg = None

            exact_dtype = True
            if isinstance(actual, torch.Tensor):
                _helper_reference_numerics(
                    expected, actual, msg, exact_dtype, equal_nan
                )
            else:
                for x, y in zip(expected, actual):
                    # testing multi-outputs results
                    _helper_reference_numerics(x, y, msg, exact_dtype, equal_nan)