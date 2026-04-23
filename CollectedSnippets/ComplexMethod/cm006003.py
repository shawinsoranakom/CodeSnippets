def test_should_have_required_inputs(self):
        """Test that component has all required inputs."""
        input_names = {i.name for i in AMapComponent.inputs}

        assert "model" in input_names
        assert "api_key" in input_names
        assert "source" in input_names
        assert "schema" in input_names
        assert "instructions" in input_names
        assert "append_to_input_columns" in input_names