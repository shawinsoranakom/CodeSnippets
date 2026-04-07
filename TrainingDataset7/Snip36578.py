def test_import_string(self):
        cls = import_string("django.utils.module_loading.import_string")
        self.assertEqual(cls, import_string)

        # Test exceptions raised
        with self.assertRaises(ImportError):
            import_string("no_dots_in_path")
        msg = 'Module "utils_tests" does not define a "unexistent" attribute'
        with self.assertRaisesMessage(ImportError, msg):
            import_string("utils_tests.unexistent")