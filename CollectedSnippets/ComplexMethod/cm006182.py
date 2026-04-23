async def test_openai_responses_streaming(client: AsyncClient, created_api_key):
    """Test the OpenAI-compatible streaming responses endpoint directly."""
    flow, headers = await load_and_prepare_flow(client, created_api_key)

    # Now test the OpenAI-compatible streaming endpoint
    payload = {"model": flow["id"], "input": "Hello, stream!", "stream": True}

    # Make the request
    response = await client.post("/api/v1/responses", json=payload, headers=headers)
    logger.info(f"Response status: {response.status_code}")

    # Handle potential errors
    if response.status_code != 200:
        logger.error(f"Error response: {response.content}")
        pytest.fail(f"Request failed with status {response.status_code}")

    # For streaming, we should get a stream of server-sent events
    content = await response.aread()
    text_content = content.decode("utf-8")
    logger.debug(f"Response content (first 200 chars): {text_content[:200]}")

    # Check that we got some SSE data events
    assert "data:" in text_content

    # Parse the events to validate structure and final [DONE] marker
    events = text_content.strip().split("\n\n")
    # The stream must end with the OpenAI '[DONE]' sentinel
    assert events, "No events in stream"
    assert events[-1].strip() == "data: [DONE]", "Stream did not end with [DONE] marker"

    # Filter out the [DONE] marker to inspect JSON data events
    data_events = [evt for evt in events if evt.startswith("data:") and not evt.startswith("data: [DONE]")]
    assert data_events, "No streaming events were received"

    # Parse the first and last JSON events to check their structure
    first_event = json.loads(data_events[0].replace("data: ", ""))
    last_event = json.loads(data_events[-1].replace("data: ", ""))
    assert "delta" in first_event
    assert "delta" in last_event

    # Check for response.completed event with usage (if present)
    completed_events = [evt for evt in events if "event: response.completed" in evt]
    if completed_events:
        # Parse the response.completed event
        for line in completed_events[0].split("\n"):
            if line.startswith("data:"):
                completed_data = json.loads(line.replace("data: ", ""))
                assert "response" in completed_data
                assert "usage" in completed_data["response"]
                if completed_data["response"]["usage"] is not None:
                    logger.info(f"Streaming usage data returned: {completed_data['response']['usage']}")
                break