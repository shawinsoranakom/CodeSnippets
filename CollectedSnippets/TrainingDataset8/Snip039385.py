def test_compiled_ffi_not_hashable(self):
        self._build_cffi("foo")
        from cffi_bin._foo import ffi as foo

        with self.assertRaises(UnhashableTypeError):
            get_hash(foo)