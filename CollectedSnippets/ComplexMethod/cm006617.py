def test_inputs_defined(self, wx_embeddings_component):
        """Test that all required inputs are defined."""
        input_names = [inp.name for inp in wx_embeddings_component.inputs]

        # Check for required inputs
        assert "url" in input_names
        assert "project_id" in input_names
        assert "space_id" in input_names
        assert "api_key" in input_names
        assert "model_name" in input_names
        assert "truncate_input_tokens" in input_names
        assert "input_text" in input_names