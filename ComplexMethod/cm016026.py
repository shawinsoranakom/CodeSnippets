def test_shift_all_bits(self, type_code, op):
        """Shifts where the shift amount is the width of the type or wider"""
        # gh-2449
        dt = np.dtype(type_code)
        nbits = dt.itemsize * 8
        if dt in (np.dtype(np.uint64), np.dtype(np.uint32), np.dtype(np.uint16)):
            raise SkipTest("NYI: bitshift uint64")

        for val in [5, -5]:
            for shift in [nbits, nbits + 4]:
                val_scl = np.array(val).astype(dt)[()]
                shift_scl = dt.type(shift)

                res_scl = op(val_scl, shift_scl)
                if val_scl < 0 and op is operator.rshift:
                    # sign bit is preserved
                    assert_equal(res_scl, -1)
                else:
                    if type_code in ("i", "l") and shift == np.iinfo(type_code).bits:
                        # FIXME: make xfail
                        raise SkipTest(
                            "https://github.com/pytorch/pytorch/issues/70904"
                        )
                    assert_equal(res_scl, 0)

                # Result on scalars should be the same as on arrays
                val_arr = np.array([val_scl] * 32, dtype=dt)
                shift_arr = np.array([shift] * 32, dtype=dt)
                res_arr = op(val_arr, shift_arr)
                assert_equal(res_arr, res_scl)