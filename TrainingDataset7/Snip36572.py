def test_loader(self):
        "Normal module existence can be tested"
        test_module = import_module("utils_tests.test_module")
        test_no_submodule = import_module("utils_tests.test_no_submodule")

        # An importable child
        self.assertTrue(module_has_submodule(test_module, "good_module"))
        mod = import_module("utils_tests.test_module.good_module")
        self.assertEqual(mod.content, "Good Module")

        # A child that exists, but will generate an import error if loaded
        self.assertTrue(module_has_submodule(test_module, "bad_module"))
        with self.assertRaises(ImportError):
            import_module("utils_tests.test_module.bad_module")

        # A child that doesn't exist
        self.assertFalse(module_has_submodule(test_module, "no_such_module"))
        with self.assertRaises(ImportError):
            import_module("utils_tests.test_module.no_such_module")

        # A child that doesn't exist, but is the name of a package on the path
        self.assertFalse(module_has_submodule(test_module, "django"))
        with self.assertRaises(ImportError):
            import_module("utils_tests.test_module.django")

        # Don't be confused by caching of import misses
        import types  # NOQA: causes attempted import of utils_tests.types

        self.assertFalse(module_has_submodule(sys.modules["utils_tests"], "types"))

        # A module which doesn't have a __path__ (so no submodules)
        self.assertFalse(module_has_submodule(test_no_submodule, "anything"))
        with self.assertRaises(ImportError):
            import_module("utils_tests.test_no_submodule.anything")