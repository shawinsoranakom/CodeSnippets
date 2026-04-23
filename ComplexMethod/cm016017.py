def test_compatible_cast(self):
        # Some types are compatible even though they are different, no
        # copy is necessary for them. This is mostly true for some integers
        def int_types(byteswap=False):
            int_types = np.typecodes["Integer"] + np.typecodes["UnsignedInteger"]
            for int_type in int_types:
                yield np.dtype(int_type)
                if byteswap:
                    yield np.dtype(int_type).newbyteorder()

        for int1 in int_types():
            for int2 in int_types(True):
                arr = np.arange(10, dtype=int1)

                for copy in self.true_vals:
                    res = np.array(arr, copy=copy, dtype=int2)
                    if not (res is not arr and res.flags.owndata):
                        raise AssertionError("res should be a new array with owndata")
                    assert_array_equal(res, arr)

                if int1 == int2:
                    # Casting is not necessary, base check is sufficient here
                    for copy in self.false_vals:
                        res = np.array(arr, copy=copy, dtype=int2)
                        if not (res is arr or res.base is arr):
                            raise AssertionError(
                                "res should be arr or share base with arr"
                            )

                    res = np.array(arr, copy=np._CopyMode.NEVER, dtype=int2)
                    if not (res is arr or res.base is arr):
                        raise AssertionError("res should be arr or share base with arr")

                else:
                    # Casting is necessary, assert copy works:
                    for copy in self.false_vals:
                        res = np.array(arr, copy=copy, dtype=int2)
                        if not (res is not arr and res.flags.owndata):
                            raise AssertionError(
                                "res should be a new array with owndata"
                            )
                        assert_array_equal(res, arr)

                    assert_raises(
                        ValueError, np.array, arr, copy=np._CopyMode.NEVER, dtype=int2
                    )
                    assert_raises(ValueError, np.array, arr, copy=None, dtype=int2)