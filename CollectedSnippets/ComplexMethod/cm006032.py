async def test_update_build_config_adds_missing_keys(self):
        """Test that update_build_config automatically adds missing required keys with defaults."""
        component = RunFlowComponent()
        build_config = dotdict({})  # Empty config

        result = await component.update_build_config(
            build_config=build_config, field_value=None, field_name="flow_name_selected"
        )

        # Verify that all default keys are now present
        for key in component.default_keys:
            assert key in result, f"Expected key '{key}' to be added to build_config"

        # Verify specific default values
        assert result["flow_name_selected"]["options"] == []
        assert result["flow_name_selected"]["options_metadata"] == []
        assert result["flow_name_selected"]["value"] is None
        assert result["flow_id_selected"]["value"] is None
        assert result["cache_flow"]["value"] is False