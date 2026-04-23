async def test_inputs_configuration(self, component_class, default_kwargs):
        """Test that inputs are properly configured."""
        component = await self.component_setup(component_class, default_kwargs)
        assert len(component.inputs) == 2

        input_names = [inp.name for inp in component.inputs]
        assert "input_message" in input_names
        assert "ignored_message" in input_names

        # Test input_message configuration
        input_message = next(inp for inp in component.inputs if inp.name == "input_message")
        assert input_message.display_name == "Input Message"
        assert input_message.required is True
        assert "message to be passed forward" in input_message.info

        # Test ignored_message configuration
        ignored_message = next(inp for inp in component.inputs if inp.name == "ignored_message")
        assert ignored_message.display_name == "Ignored Message"
        assert ignored_message.advanced is True
        assert "workaround for continuity" in ignored_message.info