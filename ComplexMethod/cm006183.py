async def test_telemetry_http_request_format(self):
        """Integration test verifying the exact HTTP request sent to Scarf."""
        # Create service
        telemetry_service = TelemetryService.__new__(TelemetryService)
        telemetry_service.base_url = "https://mock-telemetry.example.com"
        telemetry_service.do_not_track = False
        telemetry_service.client_type = "oss"
        telemetry_service.common_telemetry_fields = {
            "langflow_version": "1.0.0",
            "platform": "python_package",
            "os": "darwin",
        }

        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        telemetry_service.client = mock_client

        # Create a real exception to get realistic stack trace
        try:

            def nested_function():
                msg = "Integration test exception"
                raise ValueError(msg)

            nested_function()
        except ValueError as exc:
            real_exc = exc

        # Mock _queue_event to directly call send_telemetry_data
        async def mock_queue_event(event_tuple):
            func, payload, path = event_tuple
            await func(payload, path)

        telemetry_service._queue_event = mock_queue_event

        # Test the full flow
        await telemetry_service.log_exception(real_exc, "lifespan")

        # Verify the exact HTTP request that would be sent to Scarf
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args

        # Verify URL
        assert call_args[0][0] == "https://mock-telemetry.example.com/exception"

        # Verify parameters match our schema
        params = call_args[1]["params"]
        assert params["exceptionType"] == "ValueError"
        assert "Integration test exception" in params["exceptionMessage"]
        assert params["exceptionContext"] == "lifespan"
        assert "stackTraceHash" in params
        assert len(params["stackTraceHash"]) == 16