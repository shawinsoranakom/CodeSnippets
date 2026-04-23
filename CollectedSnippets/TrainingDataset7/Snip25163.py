def test_ignores_non_mo_files(self):
        gettext_module._translations = {"foo": "bar"}
        path = Path("test.py")
        self.assertIsNone(translation_file_changed(None, path))
        self.assertEqual(gettext_module._translations, {"foo": "bar"})