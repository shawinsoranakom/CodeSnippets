def test_inputs_defined(self, wx_component):
        """Test that all required inputs are defined."""
        input_names = [inp.name for inp in wx_component.inputs]

        # Check for required inputs
        assert "base_url" in input_names
        assert "project_id" in input_names
        assert "space_id" in input_names
        assert "api_key" in input_names
        assert "model_name" in input_names
        assert "max_tokens" in input_names
        assert "temperature" in input_names
        assert "top_p" in input_names
        assert "stream" in input_names