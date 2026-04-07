def test_module_no_spec(self):
        module = types.ModuleType("test_module")
        del module.__spec__
        with mock.patch.dict(sys.modules, {"__main__": module}):
            self.assertEqual(
                autoreload.get_child_arguments(),
                [sys.executable, __file__, "runserver"],
            )