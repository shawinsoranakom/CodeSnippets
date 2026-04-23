def test_should_create_with_required_field_only(self):
        """Should create request with only required flow_id field."""
        request = AssistantRequest(flow_id="test-flow-id")

        assert request.flow_id == "test-flow-id"
        assert request.component_id is None
        assert request.field_name is None
        assert request.input_value is None
        assert request.max_retries is None
        assert request.model_name is None
        assert request.provider is None
        assert request.session_id is None