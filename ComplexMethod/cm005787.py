async def test_log_exception_method(self):
        """Test the log_exception method creates proper payload."""
        # Create a minimal telemetry service for testing
        telemetry_service = TelemetryService.__new__(TelemetryService)
        telemetry_service.do_not_track = False
        telemetry_service._stopping = False
        telemetry_service.client_type = "oss"

        # Mock the _queue_event method to capture calls
        captured_events = []

        async def mock_queue_event(event_tuple):
            captured_events.append(event_tuple)

        telemetry_service._queue_event = mock_queue_event

        # Test exception
        test_exception = RuntimeError("Test exception message")

        # Call log_exception
        await telemetry_service.log_exception(test_exception, "handler")

        # Verify event was queued
        assert len(captured_events) == 1

        _func, payload, path = captured_events[0]

        # Verify payload
        assert isinstance(payload, ExceptionPayload)
        assert payload.exception_type == "RuntimeError"
        assert payload.exception_message == "Test exception message"
        assert payload.exception_context == "handler"
        assert payload.stack_trace_hash is not None
        assert len(payload.stack_trace_hash) == 16  # MD5 hash truncated to 16 chars

        # Verify path
        assert path == "exception"