def test_component_input_types(self, component_class):
        """Test that inputs have correct types."""
        component = component_class()

        # Find specific inputs by name
        api_key_input = next(input_ for input_ in component.inputs if input_.name == "api_key")
        model_name_input = next(input_ for input_ in component.inputs if input_.name == "model_name")
        temperature_input = next(input_ for input_ in component.inputs if input_.name == "temperature")

        assert api_key_input.field_type.value == "str"  # SecretStrInput
        assert model_name_input.field_type.value == "str"  # DropdownInput (actually returns "str")
        assert temperature_input.field_type.value == "slider"