def test_dynamic_imports_mapping_complete(self):
        """Test that _dynamic_imports mapping is complete for all categories."""
        failed_mappings = []

        for category_name in components.__all__:
            try:
                category_module = getattr(components, category_name)

                if hasattr(category_module, "__all__") and hasattr(category_module, "_dynamic_imports"):
                    category_all = set(category_module.__all__)
                    dynamic_imports_keys = set(category_module._dynamic_imports.keys())

                    # Check that all items in __all__ have corresponding _dynamic_imports entries
                    missing_in_dynamic = category_all - dynamic_imports_keys
                    if missing_in_dynamic:
                        failed_mappings.append(f"{category_name}: Missing in _dynamic_imports: {missing_in_dynamic}")

                    # Check that all _dynamic_imports keys are in __all__
                    missing_in_all = dynamic_imports_keys - category_all
                    if missing_in_all:
                        failed_mappings.append(f"{category_name}: Missing in __all__: {missing_in_all}")

            except Exception as e:
                failed_mappings.append(f"{category_name}: Error checking mappings: {e!s}")

        if failed_mappings:
            pytest.fail(f"Inconsistent mappings: {failed_mappings}")