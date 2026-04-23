async def test_inputs_configuration(self, component_class, default_kwargs):
        """Test that inputs are properly configured."""
        component = await self.component_setup(component_class, default_kwargs)
        assert len(component.inputs) == 4

        input_names = [inp.name for inp in component.inputs]
        expected_inputs = ["data_input", "key_name", "operator", "compare_value"]
        for expected_input in expected_inputs:
            assert expected_input in input_names

        # Test data_input configuration
        data_input = next(inp for inp in component.inputs if inp.name == "data_input")
        assert data_input.is_list is True