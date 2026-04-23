def test_binary_ufunc_dtype_and_out(self):
        # all in float64: no precision loss
        out64 = np.empty(2, dtype=np.float64)
        r64 = np.add([1.0, 2.0], 1.0e-15, out=out64)

        if not (r64 != [1.0, 2.0]).all():
            raise AssertionError("Expected r64 != [1.0, 2.0]")
        if r64.dtype != np.float64:
            raise AssertionError(f"Expected dtype float64, got {r64.dtype}")

        # all in float32: loss of precision, result is float32
        out32 = np.empty(2, dtype=np.float32)
        r32 = np.add([1.0, 2.0], 1.0e-15, dtype=np.float32, out=out32)
        if not (r32 == [1, 2]).all():
            raise AssertionError("Expected r32 == [1, 2]")
        if r32.dtype != np.float32:
            raise AssertionError(f"Expected dtype float32, got {r32.dtype}")

        # dtype is float32, so computation is in float32: precision loss
        # the result is then cast to float64
        out64 = np.empty(2, dtype=np.float64)
        r = np.add([1.0, 2.0], 1.0e-15, dtype=np.float32, out=out64)
        if not (r == [1, 2]).all():
            raise AssertionError("Expected r == [1, 2]")
        if r.dtype != np.float64:
            raise AssertionError(f"Expected dtype float64, got {r.dtype}")

        # Internal computations are in float64, but the final cast to out.dtype
        # truncates the precision => precision loss.
        out32 = np.empty(2, dtype=np.float32)
        r = np.add([1.0, 2.0], 1.0e-15, dtype=np.float64, out=out32)
        if not (r == [1, 2]).all():
            raise AssertionError("Expected r == [1, 2]")
        if r.dtype != np.float32:
            raise AssertionError(f"Expected dtype float32, got {r.dtype}")