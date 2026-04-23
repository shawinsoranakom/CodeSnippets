async def test_sampling_callback_exception(self, mock_bridge):
        """Test sampling callback with exception"""
        callback = create_sampling_callback(mock_bridge)

        # Create mock context that raises exception
        mock_context = AsyncMock(spec=RequestContext)

        # Create params that will cause an exception when accessing
        mock_params = MagicMock()
        mock_params.messages = None  # This should cause an error

        # Mock the model_dump to raise exception
        mock_params.model_dump.side_effect = Exception("Test sampling error")

        result = await callback(mock_context, mock_params)

        # Verify result is ErrorData
        assert isinstance(result, ErrorData)
        assert result.code == -32603
        assert "Sampling failed" in result.message

        # Verify error was logged
        error_events = [e for e in mock_bridge.events if e[1] == "error"]
        assert len(error_events) == 1
        assert "Sampling callback error" in error_events[0][2]