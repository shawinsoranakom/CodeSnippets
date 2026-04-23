def test_multiple_category_modules(self):
        """Test dynamic imports work across multiple category modules."""
        import lfx.components.anthropic as anthropic_components
        import lfx.components.data as data_components

        # Test different categories work independently
        # AnthropicModelComponent should work if anthropic library is available
        try:
            anthropic_component = anthropic_components.AnthropicModelComponent
            # If it succeeds, just check it's a valid component
            assert anthropic_component is not None
            assert hasattr(anthropic_component, "__name__")
        except AttributeError:
            # If it fails due to missing dependencies, that's also expected
            pass

        # APIRequestComponent should work now that validators is installed
        api_component = data_components.APIRequestComponent
        assert api_component is not None
        assert hasattr(api_component, "__name__")

        # Test that __all__ still works correctly despite import failures
        assert "AnthropicModelComponent" in anthropic_components.__all__
        assert "APIRequestComponent" in data_components.__all__