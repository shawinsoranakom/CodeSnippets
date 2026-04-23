async def test_new_input_fields_present(self, component_class, default_kwargs):
        """Test that new input fields are present in the component.

        This test verifies that all the new input fields specific to the Cuga
        component are properly defined and have correct default values.
        """
        component = await self.component_setup(component_class, default_kwargs)

        input_names = [inp.name for inp in component.inputs if hasattr(inp, "name")]

        # Test for new fields specific to Cuga
        assert "instructions" in input_names
        assert "n_messages" in input_names
        assert "browser_enabled" in input_names
        assert "web_apps" in input_names
        assert "lite_mode" in input_names
        assert "lite_mode_tool_threshold" in input_names
        assert "decomposition_strategy" in input_names

        # Verify default values
        assert hasattr(component, "instructions")
        assert hasattr(component, "n_messages")
        assert hasattr(component, "browser_enabled")
        assert hasattr(component, "web_apps")
        assert hasattr(component, "lite_mode")
        assert hasattr(component, "lite_mode_tool_threshold")
        assert hasattr(component, "decomposition_strategy")
        assert component.n_messages == 100
        assert component.browser_enabled is False
        assert component.lite_mode is True
        assert component.lite_mode_tool_threshold == 25
        assert component.decomposition_strategy == "flexible"