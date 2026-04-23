async def _run_single_stream_test(client: AsyncClient, flow_id: str, headers: dict, payload: dict):
    """Helper coroutine to run and validate a single streaming request."""
    received_events = []  # Track all event types in sequence
    got_end_event = False
    final_result = None

    async with client.stream("POST", f"/api/v1/run/{flow_id}?stream=true", headers=headers, json=payload) as response:
        assert response.status_code == status.HTTP_200_OK, (
            f"Request failed with status {response.status_code}: {response.text}"
        )
        assert response.headers["content-type"].startswith("text/event-stream"), (
            f"Expected event stream content type, got: {response.headers['content-type']}"
        )

        async for line in response.aiter_lines():
            if not line or line.strip() == "":
                continue

            try:
                event_data = json.loads(line)
            except json.JSONDecodeError:
                pytest.fail(f"Failed to parse JSON from stream line: {line}")

            assert "event" in event_data, f"Event type missing in response line: {line}"
            event_type = event_data["event"]
            received_events.append(event_type)

            if event_type == "add_message":
                message_data = event_data["data"]
                assert "sender_name" in message_data, f"Missing 'sender_name' in add_message event: {message_data}"
                assert "sender" in message_data, f"Missing 'sender' in add_message event: {message_data}"
                assert "session_id" in message_data, f"Missing 'session_id' in add_message event: {message_data}"
                assert "text" in message_data, f"Missing 'text' in add_message event: {message_data}"

            elif event_type == "token":
                token_data = event_data["data"]
                assert "chunk" in token_data, f"Missing 'chunk' in token event: {token_data}"

            elif event_type == "end":
                got_end_event = True
                final_result = event_data["data"].get("result")
                assert final_result is not None, "End event should contain result data but was None"
                break  # Exit loop after end event

            elif event_type == "error":
                pytest.fail(f"Received error event in stream: {event_data['data']}")

    # Assert we got the end event
    assert got_end_event, f"Stream did not receive an end event. Received events: {received_events}"

    # Verify event sequence
    assert "end" in received_events, f"End event missing from event sequence. Received: {received_events}"
    assert received_events[-1] == "end", f"Last event should be 'end', but was '{received_events[-1]}'"

    # Verify we got at least one message or token event before end
    assert len(received_events) > 2, f"Should receive multiple events before the end event. Got: {received_events}"
    assert any(event == "add_message" for event in received_events), (
        f"Should receive at least one add_message event. Received events: {received_events}"
    )
    assert any(event == "token" for event in received_events), (
        f"Should receive at least one token event. Received events: {received_events}"
    )

    # Verify the final result structure in the end event
    assert final_result is not None, "Final result should not be None"
    assert "outputs" in final_result, f"Missing 'outputs' in final result: {final_result}"
    assert "session_id" in final_result, f"Missing 'session_id' in final result: {final_result}"
    outputs = final_result["outputs"]
    assert len(outputs) == 1, f"Expected 1 output, got {len(outputs)}: {outputs}"
    outputs_dict = outputs[0]

    # Verify the debug outputs in final result
    assert "inputs" in outputs_dict, f"Missing 'inputs' in outputs_dict: {outputs_dict}"
    assert "outputs" in outputs_dict, f"Missing 'outputs' in outputs_dict: {outputs_dict}"
    assert outputs_dict["inputs"] == {"input_value": payload["input_value"]}, (
        f"Input value mismatch. Expected: {{'input_value': {payload['input_value']}}}, Got: {outputs_dict['inputs']}"
    )
    assert isinstance(outputs_dict.get("outputs"), list), (
        f"Expected outputs to be a list, got: {type(outputs_dict.get('outputs'))}"
    )

    chat_input_outputs = [output for output in outputs_dict.get("outputs") if "ChatInput" in output.get("component_id")]
    assert len(chat_input_outputs) == 1, (
        f"Expected 1 ChatInput output, got {len(chat_input_outputs)}: {chat_input_outputs}"
    )
    assert all(
        output.get("results").get("message").get("text") == payload["input_value"] for output in chat_input_outputs
    ), f"Message text mismatch. Expected: {payload['input_value']}, Got: {chat_input_outputs}"