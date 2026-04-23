def test_basic_setup(self, component_class, default_kwargs):
        """Test basic component initialization."""
        component = component_class()
        component.set_attributes(default_kwargs)

        assert component.display_name == "CometAPI"
        assert component.description == "All AI Models in One API 500+ AI Models"
        assert component.icon == "CometAPI"
        assert component.name == "CometAPIModel"
        assert component.api_key == "test-cometapi-key"
        assert component.model_name == "gpt-4o-mini"
        assert component.temperature == 0.7
        assert component.max_tokens == 1000
        assert component.seed == 1
        assert component.json_mode is False
        assert component.app_name == "test-app"