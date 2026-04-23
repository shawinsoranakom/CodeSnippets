def test_wildcard_reexport_modules_importable(self):
        """Test that modules using wildcard imports work correctly."""
        successful_imports = 0

        for langflow_module, lfx_module in self.WILDCARD_REEXPORT_MODULES.items():
            try:
                # Import the langflow module
                lf_module = importlib.import_module(langflow_module)
                assert lf_module is not None, f"Langflow module {langflow_module} is None"

                # Wildcard imports should expose most/all attributes from lfx module
                lfx_mod = importlib.import_module(lfx_module)

                # Check that all attributes are available
                if hasattr(lfx_mod, "__all__"):
                    all_attrs = list(lfx_mod.__all__)  # Test all attributes
                    for attr in all_attrs:
                        if hasattr(lfx_mod, attr):
                            assert hasattr(lf_module, attr), f"Attribute {attr} missing from {langflow_module}"

                successful_imports += 1

            except Exception as e:
                pytest.fail(f"Failed to import wildcard re-export module {langflow_module}: {e!s}")