def test_order_mismatch(self, arr, order1, order2):
        # The order is the main (python side) reason that can cause
        # a never-copy to fail.
        # Prepare C-order, F-order and non-contiguous arrays:
        arr = arr.copy(order1)
        if order1 == "C":
            if not arr.flags.c_contiguous:
                raise AssertionError("arr should be C contiguous")
        elif order1 == "F":
            if not arr.flags.f_contiguous:
                raise AssertionError("arr should be F contiguous")
        elif arr.ndim != 0:
            # Make array non-contiguous
            arr = arr[::2, ::2]
            if arr.flags.forc:
                raise AssertionError("arr should not be forc")

        # Whether a copy is necessary depends on the order of arr:
        if order2 == "C":
            no_copy_necessary = arr.flags.c_contiguous
        elif order2 == "F":
            no_copy_necessary = arr.flags.f_contiguous
        else:
            # Keeporder and Anyorder are OK with non-contiguous output.
            # This is not consistent with the `astype` behaviour which
            # enforces contiguity for "A". It is probably historic from when
            # "K" did not exist.
            no_copy_necessary = True

        # Test it for both the array and a memoryview
        for view in [arr, memoryview(arr)]:
            for copy in self.true_vals:
                res = np.array(view, copy=copy, order=order2)
                if not (res is not arr and res.flags.owndata):
                    raise AssertionError("res should be a new array with owndata")
                assert_array_equal(arr, res)

            if no_copy_necessary:
                for copy in self.false_vals:
                    res = np.array(view, copy=copy, order=order2)
                    # res.base.obj refers to the memoryview
                    if not IS_PYPY:
                        if not (res is arr or res.base.obj is arr):
                            raise AssertionError(
                                "res should be arr or share base with arr"
                            )

                res = np.array(view, copy=np._CopyMode.NEVER, order=order2)
                if not IS_PYPY:
                    if not (res is arr or res.base.obj is arr):
                        raise AssertionError("res should be arr or share base with arr")
            else:
                for copy in self.false_vals:
                    res = np.array(arr, copy=copy, order=order2)
                    assert_array_equal(arr, res)
                assert_raises(
                    ValueError, np.array, view, copy=np._CopyMode.NEVER, order=order2
                )
                assert_raises(ValueError, np.array, view, copy=None, order=order2)