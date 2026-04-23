async def test_sampling_callback_success(self, mock_bridge):
        """Test sampling callback success case"""
        callback = create_sampling_callback(mock_bridge)

        # Create mock context and params
        mock_context = AsyncMock(spec=RequestContext)
        mock_params = CreateMessageRequestParams(
            messages=[],  # Empty messages array for test
            maxTokens=100
        )

        result = await callback(mock_context, mock_params)

        # Verify result is CreateMessageResult
        assert isinstance(result, CreateMessageResult)
        assert result.role == "assistant"
        assert result.model == "autogen-studio-default"
        assert isinstance(result.content, TextContent)
        assert "AutoGen Studio Default Sampling Response" in result.content.text

        # Verify activities were logged
        assert len(mock_bridge.events) == 2
        # First event: sampling request
        assert mock_bridge.events[0][1] == "sampling"
        assert "Tool requested AI sampling" in mock_bridge.events[0][2]
        # Second event: sampling response
        assert mock_bridge.events[1][1] == "sampling"
        assert "Provided default sampling response" in mock_bridge.events[1][2]