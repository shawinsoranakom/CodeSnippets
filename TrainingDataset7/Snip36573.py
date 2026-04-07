def test_has_sumbodule_with_dotted_path(self):
        """Nested module existence can be tested."""
        test_module = import_module("utils_tests.test_module")
        # A grandchild that exists.
        self.assertIs(
            module_has_submodule(test_module, "child_module.grandchild_module"), True
        )
        # A grandchild that doesn't exist.
        self.assertIs(
            module_has_submodule(test_module, "child_module.no_such_module"), False
        )
        # A grandchild whose parent doesn't exist.
        self.assertIs(
            module_has_submodule(test_module, "no_such_module.grandchild_module"), False
        )
        # A grandchild whose parent is not a package.
        self.assertIs(
            module_has_submodule(test_module, "good_module.no_such_module"), False
        )