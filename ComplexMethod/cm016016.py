def _clip_type(
        self,
        type_group,
        array_max,
        clip_min,
        clip_max,
        inplace=False,
        expected_min=None,
        expected_max=None,
    ):
        if expected_min is None:
            expected_min = clip_min
        if expected_max is None:
            expected_max = clip_max

        for T in _sctypes[type_group]:
            if sys.byteorder == "little":
                byte_orders = ["=", ">"]
            else:
                byte_orders = ["<", "="]

            for byteorder in byte_orders:
                dtype = np.dtype(T).newbyteorder(byteorder)

                x = (np.random.random(1000) * array_max).astype(dtype)
                if inplace:
                    # The tests that call us pass clip_min and clip_max that
                    # might not fit in the destination dtype. They were written
                    # assuming the previous unsafe casting, which now must be
                    # passed explicitly to avoid a warning.
                    x.clip(clip_min, clip_max, x, casting="unsafe")
                else:
                    x = x.clip(clip_min, clip_max)
                    byteorder = "="

                if x.dtype.byteorder == "|":
                    byteorder = "|"
                assert_equal(x.dtype.byteorder, byteorder)
                self._check_range(x, expected_min, expected_max)
        return x