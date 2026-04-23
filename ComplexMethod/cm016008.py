def test_reshape_method(self):
        arr = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]])
        arr_shape = arr.shape

        tgt = [[1, 2, 3, 4, 5, 6], [7, 8, 9, 10, 11, 12]]

        # reshape(*shape_tuple)
        if not np.all(arr.reshape(2, 6) == tgt):
            raise AssertionError("reshape(2, 6) result does not match expected")
        if arr.reshape(2, 6).tensor._base is not arr.tensor:  # reshape keeps the base
            raise AssertionError("Expected reshape tensor._base to be arr.tensor")
        if arr.shape != arr_shape:  # arr is intact
            raise AssertionError(f"Expected shape {arr_shape}, got {arr.shape}")

        # XXX: move out to dedicated test(s)
        if arr.reshape(2, 6).tensor._base is not arr.tensor:
            raise AssertionError("Expected reshape tensor._base to be arr.tensor")

        # reshape(shape_tuple)
        if not np.all(arr.reshape((2, 6)) == tgt):
            raise AssertionError("reshape((2, 6)) result does not match expected")
        if arr.reshape((2, 6)).tensor._base is not arr.tensor:
            raise AssertionError("Expected reshape tensor._base to be arr.tensor")
        if arr.shape != arr_shape:
            raise AssertionError(f"Expected shape {arr_shape}, got {arr.shape}")

        tgt = [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]
        if not np.all(arr.reshape(3, 4) == tgt):
            raise AssertionError("reshape(3, 4) result does not match expected")
        if arr.reshape(3, 4).tensor._base is not arr.tensor:
            raise AssertionError("Expected reshape tensor._base to be arr.tensor")
        if arr.shape != arr_shape:
            raise AssertionError(f"Expected shape {arr_shape}, got {arr.shape}")

        if not np.all(arr.reshape((3, 4)) == tgt):
            raise AssertionError("reshape((3, 4)) result does not match expected")
        if arr.reshape((3, 4)).tensor._base is not arr.tensor:
            raise AssertionError("Expected reshape tensor._base to be arr.tensor")
        if arr.shape != arr_shape:
            raise AssertionError(f"Expected shape {arr_shape}, got {arr.shape}")