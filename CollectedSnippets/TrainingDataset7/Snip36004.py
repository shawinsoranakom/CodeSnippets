def test_main_module_is_resolved(self):
        main_module = sys.modules["__main__"]
        self.assertFileFound(Path(main_module.__file__))