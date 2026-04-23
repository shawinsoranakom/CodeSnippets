def test_dir_functionality(self):
        """Test that __dir__ functionality works for all modules."""
        # Test main components module
        main_dir = dir(components)
        assert "openai" in main_dir
        assert "data" in main_dir
        assert "models_and_agents" in main_dir

        # Test category modules
        for category_name in ["openai", "data", "helpers"]:
            category_module = getattr(components, category_name)
            category_dir = dir(category_module)

            # Should include all components from __all__
            if hasattr(category_module, "__all__"):
                for component_name in category_module.__all__:
                    assert component_name in category_dir, f"{component_name} missing from dir({category_name})"