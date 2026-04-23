def test_should_create_with_all_fields(self):
        """Should create request with all fields populated."""
        request = AssistantRequest(
            flow_id="flow-123",
            component_id="comp-456",
            field_name="input_field",
            input_value="Hello, world!",
            max_retries=5,
            model_name="gpt-4",
            provider="OpenAI",
            session_id="session-789",
        )

        assert request.flow_id == "flow-123"
        assert request.component_id == "comp-456"
        assert request.field_name == "input_field"
        assert request.input_value == "Hello, world!"
        assert request.max_retries == 5
        assert request.model_name == "gpt-4"
        assert request.provider == "OpenAI"
        assert request.session_id == "session-789"