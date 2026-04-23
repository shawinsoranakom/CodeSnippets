def test_main_components_module_dynamic_import(self):
        """Test that main components module imports submodules dynamically."""
        # Import the main components module
        from lfx import components

        # Test that submodules are in __all__
        assert "models_and_agents" in components.__all__
        assert "data" in components.__all__
        assert "openai" in components.__all__

        # Access models_and_agents module - this should work via dynamic import
        models_and_agents_module = components.models_and_agents
        assert models_and_agents_module is not None

        # Should be cached in globals after access
        assert "models_and_agents" in components.__dict__
        assert components.__dict__["models_and_agents"] is models_and_agents_module

        # Second access should return cached version
        models_and_agents_module_2 = components.models_and_agents
        assert models_and_agents_module_2 is models_and_agents_module