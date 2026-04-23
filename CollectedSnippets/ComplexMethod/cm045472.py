async def test_elicitation_callback_exception(self, mock_bridge):
        """Test elicitation callback with exception"""
        callback, _ = create_elicitation_callback(mock_bridge)

        # Create mock context and params that will cause exception
        mock_context = AsyncMock(spec=RequestContext)
        mock_params = MagicMock()
        mock_params.message = "Test message"
        mock_params.requestedSchema = None

        # Mock uuid.uuid4 to raise exception
        with patch('uuid.uuid4', side_effect=Exception("UUID generation failed")):
            result = await callback(mock_context, mock_params)

        # Verify result is ErrorData
        assert isinstance(result, ErrorData)
        assert result.code == -32603
        assert "Elicitation failed" in result.message

        # Verify error was logged
        error_events = [e for e in mock_bridge.events if e[1] == "error"]
        assert len(error_events) == 1
        assert "Elicitation callback error" in error_events[0][2]