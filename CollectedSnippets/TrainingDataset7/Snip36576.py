def test_shallow_loader(self):
        "Module existence can be tested inside eggs"
        egg_name = "%s/test_egg.egg" % self.egg_dir
        with extend_sys_path(egg_name):
            egg_module = import_module("egg_module")

            # An importable child
            self.assertTrue(module_has_submodule(egg_module, "good_module"))
            mod = import_module("egg_module.good_module")
            self.assertEqual(mod.content, "Good Module")

            # A child that exists, but will generate an import error if loaded
            self.assertTrue(module_has_submodule(egg_module, "bad_module"))
            with self.assertRaises(ImportError):
                import_module("egg_module.bad_module")

            # A child that doesn't exist
            self.assertFalse(module_has_submodule(egg_module, "no_such_module"))
            with self.assertRaises(ImportError):
                import_module("egg_module.no_such_module")