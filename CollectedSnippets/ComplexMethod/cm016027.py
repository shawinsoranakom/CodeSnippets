def test_pyscalar_subclasses(self, subtype, __op__, __rop__, op, cmp):
        def op_func(self, other):
            return __op__

        def rop_func(self, other):
            return __rop__

        # Check that deferring is indicated using `__array_ufunc__`:
        myt = type(
            "myt",
            (subtype,),
            {__op__: op_func, __rop__: rop_func, "__array_ufunc__": None},
        )

        # Just like normally, we should never presume we can modify the float.
        if op(myt(1), np.float64(2)) != __op__:
            raise AssertionError(f"Expected op result == {__op__}")
        if op(np.float64(1), myt(2)) != __rop__:
            raise AssertionError(f"Expected rop result == {__rop__}")

        if op in {operator.mod, operator.floordiv} and subtype is complex:
            return  # module is not support for complex.  Do not test.

        if __rop__ == __op__:
            return

        # When no deferring is indicated, subclasses are handled normally.
        myt = type("myt", (subtype,), {__rop__: rop_func})

        # Check for float32, as a float subclass float64 may behave differently
        res = op(myt(1), np.float16(2))
        expected = op(subtype(1), np.float16(2))
        if res != expected:
            raise AssertionError(f"Expected res == {expected}, got {res}")
        if type(res) is not type(expected):
            raise AssertionError(
                f"Expected type(res) is {type(expected)}, got {type(res)}"
            )
        res = op(np.float32(2), myt(1))
        expected = op(np.float32(2), subtype(1))
        if res != expected:
            raise AssertionError(f"Expected res == {expected}, got {res}")
        if type(res) is not type(expected):
            raise AssertionError(
                f"Expected type(res) is {type(expected)}, got {type(res)}"
            )