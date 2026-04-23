def test_consistent_helper_interface(self):
        """Test all registered DSL utils expose consistent public APIs."""
        from torch.testing._internal.common_utils import get_all_dsls

        # Automatically discover all registered DSLs
        dsl_names = get_all_dsls()
        if not dsl_names:
            # Fallback to hardcoded list if registry not available
            dsl_names = ["triton", "cutedsl"]

        modules_info = [
            (f"{dsl}_utils.py", f"torch._native.{dsl}_utils") for dsl in dsl_names
        ]

        # Import modules directly to avoid dependency issues
        modules = {}
        for file_name, module_name in modules_info:
            modules[module_name] = _import_module_directly(module_name, file_name)

        required_methods = {
            "runtime_available",
            "runtime_version",
            "register_op_override",
            "deregister_op_overrides",
        }

        # Test each module has required methods and they're callable
        public_apis = {}
        for module_name, mod in modules.items():
            with self.subTest(module=module_name, test="required_methods"):
                public = {name for name in dir(mod) if not name.startswith("_")}
                public_apis[module_name] = public

                self.assertTrue(
                    required_methods <= public,
                    f"{module_name} missing: {required_methods - public}",
                )

                for method_name in required_methods:
                    with self.subTest(module=module_name, method=method_name):
                        self.assertTrue(callable(getattr(mod, method_name)))

        # Test modules expose identical public APIs
        api_sets = list(public_apis.values())
        if len(api_sets) > 1:
            for i, api_set in enumerate(api_sets[1:], 1):
                self.assertEqual(
                    api_sets[0],
                    api_set,
                    f"Module {i} should have identical public API to module 0",
                )

        # Test runtime functions return expected types
        for module_name, mod in modules.items():
            with self.subTest(module=module_name, test="runtime_functions"):
                # runtime_available should return bool
                self.assertIsInstance(mod.runtime_available(), bool)

                # runtime_version should return Version or None
                ver = mod.runtime_version()
                if ver is not None:
                    from torch._vendor.packaging.version import Version

                    self.assertIsInstance(ver, Version)