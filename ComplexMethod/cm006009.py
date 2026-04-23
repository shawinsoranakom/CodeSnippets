async def test_build_flow_loop(self, client, json_loop_test, logged_in_headers):
        """Test building a flow with a loop component."""
        # Create the flow
        flow_id = await self._create_flow(client, json_loop_test, logged_in_headers)

        # Start the build and get job_id
        build_response = await build_flow(client, flow_id, logged_in_headers)
        job_id = build_response["job_id"]
        assert job_id is not None

        # Get the events stream
        events_response = await get_build_events(client, job_id, logged_in_headers)
        assert events_response.status_code == 200

        # Process the events stream
        chat_output = None
        lines = []
        async for line in events_response.aiter_lines():
            if not line:  # Skip empty lines
                continue
            lines.append(line)
            if "ChatOutput" in line:
                chat_output = json.loads(line)
            # Process events if needed
            # We could add specific assertions here for loop-related events
        assert chat_output is not None
        messages = await self.check_messages(flow_id)
        ai_message = messages[0].text
        json_data = orjson.loads(ai_message)

        # Use a for loop for better debugging
        found = []
        json_data = [(data["text"], q_dict) for data, q_dict in json_data]
        for text, q_dict in json_data:
            expected_text = f"==> {q_dict['q']}"
            assert expected_text in text, (
                f"Found {found} until now, but expected '{expected_text}' not found in '{text}',"
                f"and the json_data is {json_data}"
            )
            found.append(expected_text)