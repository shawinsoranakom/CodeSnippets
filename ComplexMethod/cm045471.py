async def test_elicitation_callback_timeout(self, mock_bridge):
        """Test elicitation callback timeout"""
        callback, _ = create_elicitation_callback(mock_bridge)

        # Create mock context and params
        mock_context = AsyncMock(spec=RequestContext)
        mock_params = ElicitRequestParams(
            message="Please provide input",
            requestedSchema={"type": "string"}
        )

        # Mock asyncio.wait_for to raise TimeoutError
        with patch('asyncio.wait_for', side_effect=asyncio.TimeoutError):
            result = await callback(mock_context, mock_params)

        # Verify result is ErrorData
        assert isinstance(result, ErrorData)
        assert result.code == -32603
        assert "60 seconds" in result.message

        # Verify timeout was logged
        error_events = [e for e in mock_bridge.events if e[1] == "error"]
        assert len(error_events) == 1
        assert "Elicitation timeout" in error_events[0][2]