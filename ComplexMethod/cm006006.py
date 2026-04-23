async def test_inputs_configuration(self, component_class, default_kwargs):
        """Test that inputs are properly configured."""
        component = await self.component_setup(component_class, default_kwargs)
        expected_inputs = {"flow_name", "tool_name", "tool_description", "return_direct"}
        input_names = {inp.name for inp in component.inputs}

        assert expected_inputs.issubset(input_names)

        # Test flow_name input configuration
        flow_name_input = next(inp for inp in component.inputs if inp.name == "flow_name")
        assert flow_name_input.display_name == "Flow Name"
        assert flow_name_input.refresh_button is True

        # Test return_direct input configuration
        return_direct_input = next(inp for inp in component.inputs if inp.name == "return_direct")
        assert return_direct_input.advanced is True