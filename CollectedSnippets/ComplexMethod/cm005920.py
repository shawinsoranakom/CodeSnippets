def test_component_modules_have_required_attributes(self):
        """Test that component modules have required attributes for dynamic loading."""
        failed_modules = []

        for category_name in components.__all__:
            try:
                category_module = getattr(components, category_name)

                # Check for required attributes
                required_attrs = ["__all__"]

                failed_modules.extend(
                    f"{category_name}: Missing required attribute {attr}"
                    for attr in required_attrs
                    if not hasattr(category_module, attr)
                )

                # Check that if it has dynamic imports, it has the pattern
                if hasattr(category_module, "_dynamic_imports"):
                    if not hasattr(category_module, "__getattr__"):
                        failed_modules.append(f"{category_name}: Has _dynamic_imports but no __getattr__")
                    if not hasattr(category_module, "__dir__"):
                        failed_modules.append(f"{category_name}: Has _dynamic_imports but no __dir__")

            except Exception as e:
                failed_modules.append(f"{category_name}: Error checking attributes: {e!s}")

        if failed_modules:
            pytest.fail(f"Module attribute issues: {failed_modules}")