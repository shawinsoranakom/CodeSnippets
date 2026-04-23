def test_main_module_without_file_is_not_resolved(self):
        fake_main = types.ModuleType("__main__")
        self.assertEqual(
            autoreload.iter_modules_and_files((fake_main,), frozenset()), frozenset()
        )