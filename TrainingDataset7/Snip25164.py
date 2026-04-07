def test_resets_cache_with_mo_files(self):
        gettext_module._translations = {"foo": "bar"}
        trans_real._translations = {"foo": "bar"}
        trans_real._default = 1
        trans_real._active = False
        path = Path("test.mo")
        self.assertIs(translation_file_changed(None, path), True)
        self.assertEqual(gettext_module._translations, {})
        self.assertEqual(trans_real._translations, {})
        self.assertIsNone(trans_real._default)
        self.assertIsInstance(trans_real._active, Local)