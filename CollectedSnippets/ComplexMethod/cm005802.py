def test_complex_reexport_modules_importable(self):
        """Test that modules with complex/mixed import patterns work correctly."""
        successful_imports = 0

        for langflow_module in self.COMPLEX_REEXPORT_MODULES:
            try:
                # Import the langflow module
                lf_module = importlib.import_module(langflow_module)
                assert lf_module is not None, f"Langflow module {langflow_module} is None"

                # Verify it has __all__ attribute for complex modules
                assert hasattr(lf_module, "__all__"), f"Complex module {langflow_module} missing __all__"
                assert len(lf_module.__all__) > 0, f"Complex module {langflow_module} has empty __all__"

                # Try to access all items from __all__
                all_items = lf_module.__all__  # Test all items
                for item in all_items:
                    try:
                        attr = getattr(lf_module, item)
                        assert attr is not None, f"Attribute {item} is None in {langflow_module}"
                    except AttributeError:
                        pytest.fail(f"Complex module {langflow_module} missing expected attribute {item} from __all__")

                successful_imports += 1

            except Exception as e:
                pytest.fail(f"Failed to import complex re-export module {langflow_module}: {e!s}")