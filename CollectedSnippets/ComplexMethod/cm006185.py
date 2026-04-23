def test_component_payload_creation_and_serialization(self):
        """Test ComponentPayload creation and serialization with aliases."""
        payload = ComponentPayload(
            component_name="TestComponent",
            component_id="TestComponent-abc123",
            component_seconds=42,
            component_success=True,
            component_error_message="Test error",
            client_type="oss",
        )

        # Test direct attribute access
        assert payload.component_name == "TestComponent"
        assert payload.component_id == "TestComponent-abc123"
        assert payload.component_seconds == 42
        assert payload.component_success is True
        assert payload.component_error_message == "Test error"
        assert payload.client_type == "oss"

        # Test serialization with aliases
        serialized = payload.model_dump(by_alias=True)
        expected = {
            "componentName": "TestComponent",
            "componentId": "TestComponent-abc123",
            "componentSeconds": 42,
            "componentSuccess": True,
            "componentErrorMessage": "Test error",
            "clientType": "oss",
            "componentRunId": None,
        }
        assert serialized == expected