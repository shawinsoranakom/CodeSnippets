def test_stream_request_model(self):
        """Test the StreamRequest model validation."""
        # Test minimal request
        request = StreamRequest(input_value="test")
        assert request.input_value == "test"
        assert request.input_type == "chat"  # default
        assert request.output_type == "chat"  # default
        assert request.session_id is None
        assert request.tweaks is None

        # Test full request
        request = StreamRequest(
            input_value="test input",
            input_type="text",
            output_type="debug",
            output_component="specific_component",
            session_id="session123",
            tweaks={"comp1": {"param1": "value1"}},
        )
        assert request.input_value == "test input"
        assert request.input_type == "text"
        assert request.output_type == "debug"
        assert request.output_component == "specific_component"
        assert request.session_id == "session123"
        assert request.tweaks == {"comp1": {"param1": "value1"}}