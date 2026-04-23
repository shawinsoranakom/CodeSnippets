def test_compiled_ffi(self):
        self._build_cffi("foo")
        self._build_cffi("bar")
        from cffi_bin._bar import ffi as bar
        from cffi_bin._foo import ffi as foo

        # Note: We've verified that all properties on CompiledFFI objects
        # are global, except have not verified `error` either way.
        self.assertIn(get_fqn_type(foo), _FFI_TYPE_NAMES)
        self.assertEqual(get_hash(foo), get_hash(bar))