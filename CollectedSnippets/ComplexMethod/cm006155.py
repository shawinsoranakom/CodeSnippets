def test_groq_model_has_required_inputs(self, groq_model_instance):
        """Test that GroqModel has all required inputs."""
        input_names = [inp.name for inp in groq_model_instance.inputs]

        assert "api_key" in input_names
        assert "base_url" in input_names
        assert "max_tokens" in input_names
        assert "temperature" in input_names
        assert "model_name" in input_names
        assert "tool_model_enabled" in input_names