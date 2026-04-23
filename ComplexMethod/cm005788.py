async def test_send_telemetry_data_success(self):
        """Test successful telemetry data sending."""
        # Create minimal service
        telemetry_service = TelemetryService.__new__(TelemetryService)
        telemetry_service.base_url = "https://mock-telemetry.example.com"
        telemetry_service.do_not_track = False
        telemetry_service.client_type = "oss"
        telemetry_service.common_telemetry_fields = {
            "langflow_version": "1.0.0",
            "platform": "python_package",
            "os": "linux",
        }

        # Mock HTTP client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        telemetry_service.client = mock_client

        payload = ExceptionPayload(
            exception_type="ValueError",
            exception_message="Test error",
            exception_context="handler",
            stack_trace_hash="abc123",
        )

        # Send telemetry
        await telemetry_service.send_telemetry_data(payload, "exception")

        # Verify HTTP call was made
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args

        # Check URL
        assert call_args[0][0] == "https://mock-telemetry.example.com/exception"

        # Check query parameters (should include common telemetry fields)
        params = call_args[1]["params"]
        assert params["exceptionType"] == "ValueError"
        assert params["exceptionMessage"] == "Test error"
        assert params["exceptionContext"] == "handler"
        assert params["stackTraceHash"] == "abc123"
        assert params["clientType"] == "oss"
        assert params["langflow_version"] == "1.0.0"
        assert params["platform"] == "python_package"
        assert params["os"] == "linux"
        assert "timestamp" in params