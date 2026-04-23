def test_inputs(self):
        component = XAIModelComponent()
        inputs = component.inputs
        expected_inputs = {
            "max_tokens": IntInput,
            "model_kwargs": DictInput,
            "json_mode": BoolInput,
            "model_name": DropdownInput,
            "base_url": MessageTextInput,
            "api_key": SecretStrInput,
            "temperature": SliderInput,
            "seed": IntInput,
        }
        for name, input_type in expected_inputs.items():
            matching_inputs = [inp for inp in inputs if isinstance(inp, input_type) and inp.name == name]
            assert matching_inputs, f"Missing or incorrect input: {name}"
            if name == "model_name":
                input_field = matching_inputs[0]
                assert input_field.value == "grok-2-latest"
                assert input_field.refresh_button is True
            elif name == "temperature":
                input_field = matching_inputs[0]
                assert input_field.value == 0.1
                assert input_field.range_spec.min == 0
                assert input_field.range_spec.max == 2