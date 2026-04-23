def test_np_argmin_argmax_keepdims(self, size, axis, method):
        arr = np.random.normal(size=size)
        if size is None or size == ():
            arr = np.asarray(arr)

        # contiguous arrays
        if axis is None:
            new_shape = [1 for _ in range(len(size))]
        else:
            new_shape = list(size)
            new_shape[axis] = 1
        new_shape = tuple(new_shape)

        _res_orig = method(arr, axis=axis)
        res_orig = _res_orig.reshape(new_shape)
        res = method(arr, axis=axis, keepdims=True)
        assert_equal(res, res_orig)
        assert_(res.shape == new_shape)
        outarray = np.empty(res.shape, dtype=res.dtype)
        res1 = method(arr, axis=axis, out=outarray, keepdims=True)
        assert_(res1 is outarray)
        assert_equal(res, outarray)

        if len(size) > 0:
            wrong_shape = list(new_shape)
            if axis is not None:
                wrong_shape[axis] = 2
            else:
                wrong_shape[0] = 2
            wrong_outarray = np.empty(wrong_shape, dtype=res.dtype)
            with pytest.raises(ValueError):
                method(arr.T, axis=axis, out=wrong_outarray, keepdims=True)

        # non-contiguous arrays
        if axis is None:
            new_shape = [1 for _ in range(len(size))]
        else:
            new_shape = list(size)[::-1]
            new_shape[axis] = 1
        new_shape = tuple(new_shape)

        _res_orig = method(arr.T, axis=axis)
        res_orig = _res_orig.reshape(new_shape)
        res = method(arr.T, axis=axis, keepdims=True)
        assert_equal(res, res_orig)
        assert_(res.shape == new_shape)
        outarray = np.empty(new_shape[::-1], dtype=res.dtype)
        outarray = outarray.T
        res1 = method(arr.T, axis=axis, out=outarray, keepdims=True)
        assert_(res1 is outarray)
        assert_equal(res, outarray)

        if len(size) > 0:
            # one dimension lesser for non-zero sized
            # array should raise an error
            with pytest.raises(ValueError):
                method(arr[0], axis=axis, out=outarray, keepdims=True)

        if len(size) > 0:
            wrong_shape = list(new_shape)
            if axis is not None:
                wrong_shape[axis] = 2
            else:
                wrong_shape[0] = 2
            wrong_outarray = np.empty(wrong_shape, dtype=res.dtype)
            with pytest.raises(ValueError):
                method(arr.T, axis=axis, out=wrong_outarray, keepdims=True)