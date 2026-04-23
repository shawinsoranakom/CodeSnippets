async def test_elicitation_callback_success(self, mock_bridge):
        """Test elicitation callback success case"""
        callback, pending_dict = create_elicitation_callback(mock_bridge)

        # Verify that pending_dict is the same as bridge's pending_elicitations
        assert pending_dict is mock_bridge.pending_elicitations

        # Create mock context and params
        mock_context = AsyncMock(spec=RequestContext)
        mock_params = ElicitRequestParams(
            message="Please provide your name",
            requestedSchema={"type": "string"}
        )

        # Create a task to simulate user response
        async def simulate_user_response():
            await asyncio.sleep(0.1)  # Let elicitation setup

            # Find the request ID from events
            elicit_events = [e for e in mock_bridge.events if e[0] == "elicitation_request"]
            assert len(elicit_events) == 1
            request_id = elicit_events[0][1]

            # Simulate user accepting
            if request_id in mock_bridge.pending_elicitations:
                future = mock_bridge.pending_elicitations[request_id]
                result = ElicitResult(action="accept", content={"name": "John Doe"})
                future.set_result(result)

        # Run both the callback and the response simulation
        callback_task = asyncio.create_task(callback(mock_context, mock_params))
        response_task = asyncio.create_task(simulate_user_response())

        result, _ = await asyncio.gather(callback_task, response_task)

        # Verify result
        assert isinstance(result, ElicitResult)
        assert result.action == "accept"
        assert result.content == {"name": "John Doe"}

        # Verify events were logged
        activity_events = [e for e in mock_bridge.events if e[0] == "mcp_activity"]
        elicit_events = [e for e in mock_bridge.events if e[0] == "elicitation_request"]

        assert len(elicit_events) == 1
        assert len(activity_events) >= 2