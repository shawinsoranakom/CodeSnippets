def _compare_index_result(self, arr, index, mimic_get, no_copy):
        """Compare mimicked result to indexing result."""
        raise SkipTest("torch does not support subclassing")
        arr = arr.copy()
        indexed_arr = arr[index]
        assert_array_equal(indexed_arr, mimic_get)
        # Check if we got a view, unless its a 0-sized or 0-d array.
        # (then its not a view, and that does not matter)
        if indexed_arr.size != 0 and indexed_arr.ndim != 0:
            assert_(np.may_share_memory(indexed_arr, arr) == no_copy)
            # Check reference count of the original array
            if HAS_REFCOUNT:
                if no_copy:
                    # refcount increases by one:
                    assert_equal(sys.getrefcount(arr), 3)
                else:
                    assert_equal(sys.getrefcount(arr), 2)

        # Test non-broadcast setitem:
        b = arr.copy()
        b[index] = mimic_get + 1000
        if b.size == 0:
            return  # nothing to compare here...
        if no_copy and indexed_arr.ndim != 0:
            # change indexed_arr in-place to manipulate original:
            indexed_arr += 1000
            assert_array_equal(arr, b)
            return
        # Use the fact that the array is originally an arange:
        arr.flat[indexed_arr.ravel()] += 1000
        assert_array_equal(arr, b)