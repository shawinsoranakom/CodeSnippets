def test_all_components_in_categories_importable(self):
        """Test that all components in each category's __all__ can be imported."""
        failed_imports = []
        successful_imports = 0

        print(f"Testing component imports across {len(components.__all__)} categories")  # noqa: T201

        for category_name in components.__all__:
            try:
                category_module = getattr(components, category_name)

                if hasattr(category_module, "__all__"):
                    category_components = len(category_module.__all__)
                    print(f"Testing {category_components} components in {category_name}")  # noqa: T201

                    for component_name in category_module.__all__:
                        try:
                            component = getattr(category_module, component_name)
                            assert component is not None, f"Component {component_name} is None"
                            assert callable(component), f"Component {component_name} is not callable"
                            successful_imports += 1

                        except Exception as e:
                            failed_imports.append(f"{category_name}.{component_name}: {e!s}")
                            print(f"FAILED: {category_name}.{component_name}: {e!s}")  # noqa: T201
                else:
                    # Category doesn't have __all__, skip
                    print(f"Skipping {category_name} (no __all__ attribute)")  # noqa: T201
                    continue

            except Exception as e:
                failed_imports.append(f"Category {category_name}: {e!s}")
                print(f"FAILED: Category {category_name}: {e!s}")  # noqa: T201

        print(f"Successfully imported {successful_imports} components")  # noqa: T201

        if failed_imports:
            print(f"Failed imports ({len(failed_imports)}):")  # noqa: T201
            for failure in failed_imports[:10]:  # Show first 10 failures
                print(f"  - {failure}")  # noqa: T201
            if len(failed_imports) > 10:
                print(f"  ... and {len(failed_imports) - 10} more")  # noqa: T201

            pytest.fail(f"Failed to import {len(failed_imports)} components")