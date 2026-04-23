def test_dynamic_reexport_modules_importable(self):
        """Test that modules with __getattr__ dynamic loading work correctly."""
        successful_imports = 0

        for langflow_module in self.DYNAMIC_REEXPORT_MODULES:
            try:
                # Import the langflow module
                lf_module = importlib.import_module(langflow_module)
                assert lf_module is not None, f"Langflow module {langflow_module} is None"

                # Dynamic modules should have __getattr__ method
                assert hasattr(lf_module, "__getattr__"), f"Dynamic module {langflow_module} missing __getattr__"

                # Test accessing some known attributes dynamically
                if langflow_module == "langflow.field_typing":
                    # Test some known field typing constants
                    test_attrs = ["Data", "Text", "LanguageModel"]
                    for attr in test_attrs:
                        try:
                            value = getattr(lf_module, attr)
                            assert value is not None, f"Dynamic attribute {attr} is None"
                        except AttributeError:
                            pytest.fail(f"Dynamic module {langflow_module} missing expected attribute {attr}")

                successful_imports += 1

            except Exception as e:
                pytest.fail(f"Failed to import dynamic re-export module {langflow_module}: {e!s}")