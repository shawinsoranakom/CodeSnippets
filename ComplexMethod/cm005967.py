async def test_advanced_fields_configuration(self, component_class, default_kwargs):
        """Test that browser and cuga lite fields are properly configured as advanced.

        This test verifies that browser_enabled, web_apps, lite_mode, and
        lite_mode_tool_threshold fields are all set to advanced.
        """
        component = await self.component_setup(component_class, default_kwargs)

        # Find all the advanced fields we want to test
        field_checks = {
            "browser_enabled": False,
            "web_apps": False,
            "lite_mode": False,
            "lite_mode_tool_threshold": False,
        }

        for inp in component.inputs:
            if hasattr(inp, "name") and inp.name in field_checks:
                field_checks[inp.name] = inp.advanced

        # Assert all fields are set to advanced
        assert field_checks["browser_enabled"] is True, "browser_enabled should be advanced"
        assert field_checks["web_apps"] is True, "web_apps should be advanced"
        assert field_checks["lite_mode"] is True, "lite_mode should be advanced"
        assert field_checks["lite_mode_tool_threshold"] is True, "lite_mode_tool_threshold should be advanced"