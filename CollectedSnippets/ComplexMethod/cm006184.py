async def test_exception_telemetry_service_integration(self):
        """Integration test for exception telemetry service without FastAPI."""
        # Create service with mocked dependencies
        telemetry_service = TelemetryService.__new__(TelemetryService)
        telemetry_service.base_url = "https://mock-telemetry.example.com"
        telemetry_service.do_not_track = False
        telemetry_service.client_type = "oss"
        telemetry_service.common_telemetry_fields = {
            "langflow_version": "1.0.0",
            "platform": "python_package",
            "os": "darwin",
        }

        # Mock the async queue and HTTP client
        telemetry_service.telemetry_queue = asyncio.Queue()

        # Track actual calls
        http_calls = []

        async def mock_send_data(payload, path):
            http_calls.append(
                {
                    "url": f"{telemetry_service.base_url}/{path}",
                    "payload": payload.model_dump(by_alias=True),
                    "path": path,
                }
            )

        # Mock _queue_event to call our mock directly
        async def mock_queue_event(event_tuple):
            _func, payload, path = event_tuple
            await mock_send_data(payload, path)

        telemetry_service._queue_event = mock_queue_event

        # Test with real exception
        test_exception = RuntimeError("Service integration test")
        await telemetry_service.log_exception(test_exception, "handler")

        # Verify the call was made with correct data
        assert len(http_calls) == 1
        call = http_calls[0]

        assert call["url"] == "https://mock-telemetry.example.com/exception"
        assert call["path"] == "exception"
        assert call["payload"]["exceptionType"] == "RuntimeError"
        assert call["payload"]["exceptionMessage"] == "Service integration test"
        assert call["payload"]["exceptionContext"] == "handler"
        assert "stackTraceHash" in call["payload"]