def test_compare_ufuncs(self, name, scalar, array):
        if name in corners and (
            array.dtype.name in corners[name]
            or tnp.asarray(scalar).dtype.name in corners[name]
        ):
            raise SkipTest(f"{name}(..., dtype=array.dtype)")

        try:
            state = _np._get_promotion_state()
            _np._set_promotion_state("weak")

            if name in ["matmul", "modf", "divmod", "ldexp"]:
                return
            ufunc = getattr(tnp, name)
            ufunc_numpy = getattr(_np, name)

            try:
                result = ufunc(scalar, array)
            except RuntimeError:
                # RuntimeError: "bitwise_xor_cpu" not implemented for 'ComplexDouble' etc
                result = None

            try:
                result_numpy = ufunc_numpy(scalar, array.tensor.numpy())
            except TypeError:
                # TypeError: ufunc 'hypot' not supported for the input types
                result_numpy = None

            type_mismatch = False
            expected_numpy_dtype = None
            expected_torch_dtype = None

            if result is not None and result_numpy is not None:
                expected_numpy_dtype = result_numpy.dtype
                expected_torch_dtype = result.tensor.numpy().dtype
                if IS_WINDOWS:
                    if (
                        array.tensor.numpy().dtype != _np.bool_
                        and result.tensor.numpy().dtype != result_numpy.dtype
                    ):
                        type_mismatch = True

                    if (
                        array.tensor.numpy().dtype == _np.bool_
                        and result_numpy.dtype == _np.int32
                        and result.tensor.numpy().dtype != _np.int64
                    ):
                        expected_numpy_dtype = _np.int32
                        expected_torch_dtype = tnp.int64
                        type_mismatch = True
                else:
                    if result.tensor.numpy().dtype != result_numpy.dtype:
                        type_mismatch = True

            if type_mismatch:
                raise AssertionError(
                    f"Expected result numpy dtype == {expected_numpy_dtype}, torch dtype == {expected_torch_dtype}"
                )

        finally:
            _np._set_promotion_state(state)