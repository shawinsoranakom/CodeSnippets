def test_module_without_spec(self):
        module = types.ModuleType("test_module")
        del module.__spec__
        self.assertEqual(
            autoreload.iter_modules_and_files((module,), frozenset()), frozenset()
        )