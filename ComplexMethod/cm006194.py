async def test_openai_streaming_format_comparison(client: AsyncClient, created_api_key):
    """Compare raw HTTP streaming formats between OpenAI and our API."""
    # Test input
    input_msg = "What is 25 + 17? Use your calculator tool."

    # Tools definition
    tools = [
        {
            "type": "function",
            "name": "evaluate_expression",
            "description": "Perform basic arithmetic operations on a given expression.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The arithmetic expression to evaluate (e.g., '4*4*(33/22)+12-20').",
                    }
                },
                "required": ["expression"],
            },
        }
    ]

    # Get OpenAI API key
    from tests.api_keys import get_openai_api_key

    try:
        openai_api_key = get_openai_api_key()
    except ValueError:
        pytest.skip("OPENAI_API_KEY environment variable not set")

    # === Test OpenAI's raw HTTP streaming format ===
    logger.info("=== Testing OpenAI API Raw HTTP Format ===")

    async with httpx.AsyncClient() as openai_client:
        openai_payload = {"model": "gpt-4o-mini", "input": input_msg, "tools": tools, "stream": True}

        openai_response = await openai_client.post(
            "https://api.openai.com/v1/responses",
            headers={"Authorization": f"Bearer {openai_api_key}", "Content-Type": "application/json"},
            json=openai_payload,
        )

        logger.info(f"OpenAI status: {openai_response.status_code}")
        if openai_response.status_code != 200:
            logger.error(f"OpenAI error: {openai_response.text}")
            pytest.skip("OpenAI API request failed")

        # Parse OpenAI's raw SSE stream
        openai_content = await openai_response.aread()
        openai_text = openai_content.decode("utf-8")

        openai_events = openai_text.strip().split("\n\n")
        openai_data_events = [evt for evt in openai_events if "data: " in evt and not evt.startswith("data: [DONE]")]

    # === Test Our API's streaming format ===
    logger.info("=== Testing Our API Format ===")

    flow, headers = await load_and_prepare_flow(client, created_api_key)

    our_payload = {"model": flow["id"], "input": input_msg, "stream": True, "include": ["tool_call.results"]}

    our_response = await client.post("/api/v1/responses", json=our_payload, headers=headers)
    assert our_response.status_code == 200

    our_content = await our_response.aread()
    our_text = our_content.decode("utf-8")

    our_events = our_text.strip().split("\n\n")
    our_data_events = [evt for evt in our_events if "data: " in evt and not evt.startswith("data: [DONE]")]

    # === Parse and compare events ===

    # Extract JSON data from OpenAI events
    openai_parsed = []
    for event_block in openai_data_events:
        lines = event_block.strip().split("\n")
        for line in lines:
            if line.startswith("data: "):
                try:
                    json_str = line.replace("data: ", "", 1)
                    event_data = json.loads(json_str)
                    openai_parsed.append(event_data)
                    break
                except json.JSONDecodeError:
                    continue

    # Extract JSON data from our events
    our_parsed = []
    for event_block in our_data_events:
        lines = event_block.strip().split("\n")
        for line in lines:
            if line.startswith("data: "):
                try:
                    json_str = line.replace("data: ", "", 1)
                    event_data = json.loads(json_str)
                    our_parsed.append(event_data)
                    break
                except json.JSONDecodeError:
                    continue

    # === Analysis ===
    logger.info("Event counts:")
    logger.info(f"  OpenAI: {len(openai_parsed)} events")
    logger.info(f"  Our API: {len(our_parsed)} events")

    # Check for tool call events with detailed logging
    logger.info("Detailed OpenAI event analysis:")
    output_item_added_events = [e for e in openai_parsed if e.get("type") == "response.output_item.added"]
    logger.info(f"  Found {len(output_item_added_events)} 'response.output_item.added' events")

    for i, event in enumerate(output_item_added_events):
        item = event.get("item", {})
        item_type = item.get("type", "unknown")
        logger.info(f"    Event {i}: item.type = '{item_type}'")
        logger.info(f"    Event {i}: item keys = {list(item.keys())}")
        if "name" in item:
            logger.info(f"    Event {i}: item.name = '{item.get('name')}'")
        logger.debug(f"    Event {i}: full item = {json.dumps(item, indent=6)}")

    openai_tool_events = [
        e
        for e in openai_parsed
        if e.get("type") == "response.output_item.added" and e.get("item", {}).get("type") == "tool_call"
    ]
    openai_function_events = [
        e
        for e in openai_parsed
        if e.get("type") == "response.output_item.added" and e.get("item", {}).get("type") == "function_call"
    ]

    logger.info("Detailed Our API event analysis:")
    our_output_item_added_events = [e for e in our_parsed if e.get("type") == "response.output_item.added"]
    logger.info(f"  Found {len(our_output_item_added_events)} 'response.output_item.added' events")

    for i, event in enumerate(our_output_item_added_events):
        item = event.get("item", {})
        item_type = item.get("type", "unknown")
        logger.info(f"    Event {i}: item.type = '{item_type}'")
        logger.info(f"    Event {i}: item keys = {list(item.keys())}")
        if "name" in item:
            logger.info(f"    Event {i}: item.name = '{item.get('name')}'")
        logger.debug(f"    Event {i}: full item = {json.dumps(item, indent=6)}")

    our_function_events = [
        e
        for e in our_parsed
        if e.get("type") == "response.output_item.added" and e.get("item", {}).get("type") == "function_call"
    ]

    logger.info("Tool call detection results:")
    logger.info(f"  OpenAI tool_call events: {len(openai_tool_events)}")
    logger.info(f"  OpenAI function_call events: {len(openai_function_events)}")
    logger.info(f"  Our function_call events: {len(our_function_events)}")

    # Use the correct event type for OpenAI (function_call vs tool_call)
    openai_actual_tool_events = openai_function_events if openai_function_events else openai_tool_events

    logger.info("Function call events:")
    logger.info(f"  OpenAI: {len(openai_actual_tool_events)} function call events")
    logger.info(f"  Our API: {len(our_function_events)} function call events")

    # Show event types
    openai_types = {e.get("type", e.get("object", "unknown")) for e in openai_parsed}
    our_types = {e.get("type", e.get("object", "unknown")) for e in our_parsed}

    logger.info("Event types:")
    logger.info(f"  OpenAI: {sorted(openai_types)}")
    logger.info(f"  Our API: {sorted(our_types)}")

    # Print sample events for debugging
    logger.info("Sample OpenAI events:")
    for i, event in enumerate(openai_parsed[:3]):
        logger.debug(f"  {i}: {json.dumps(event, indent=2)[:200]}...")

    logger.info("Sample Our events:")
    for i, event in enumerate(our_parsed[:3]):
        logger.debug(f"  {i}: {json.dumps(event, indent=2)[:200]}...")

    # Check delta content for duplicates/accumulation
    logger.info("Checking delta content for proper streaming:")
    delta_contents = []
    for i, event in enumerate(our_parsed):
        if event.get("object") == "response.chunk" and "delta" in event:
            delta_content = event["delta"].get("content", "")
            if delta_content:  # Only track non-empty content
                delta_contents.append(delta_content)
                logger.info(f"  Delta {i}: '{delta_content}'")

    # Check for accumulated content (bad) vs incremental content (good)
    if len(delta_contents) > 1:
        logger.info("Analyzing delta content patterns:")
        accumulated_pattern = True
        for i in range(1, len(delta_contents)):
            if not delta_contents[i].startswith(delta_contents[i - 1]):
                accumulated_pattern = False
                break

        if accumulated_pattern:
            logger.error("❌ DETECTED ACCUMULATED CONTENT PATTERN (BAD)")
            logger.error("Each delta contains the full accumulated message instead of just new content")
            logger.error("Example:")
            for i, content in enumerate(delta_contents[:3]):
                logger.error(f"  Delta {i}: '{content}'")
        else:
            logger.success("✅ DETECTED INCREMENTAL CONTENT PATTERN (GOOD)")
            logger.success("Each delta contains only new content")
    else:
        logger.info("Not enough delta content to analyze pattern")

    if openai_actual_tool_events:
        logger.info("OpenAI tool call example:")
        logger.debug(f"  {json.dumps(openai_actual_tool_events[0], indent=2)}")

    if our_function_events:
        logger.info("Our function call example:")
        logger.debug(f"  {json.dumps(our_function_events[0], indent=2)}")

    # === Validation ===

    # Basic validation
    assert len(openai_parsed) > 0, "No OpenAI events received"
    assert len(our_parsed) > 0, "No events from our API"

    # Check if both APIs produced function call events
    if len(openai_actual_tool_events) > 0:
        logger.success("✅ OpenAI produced function call events")
        if len(our_function_events) > 0:
            logger.success("✅ Our API also produced function call events")
            logger.success("✅ Both APIs support function call streaming")
        else:
            logger.error("❌ Our API did not produce function call events")
            pytest.fail("Our API should produce function call events when OpenAI does")
    else:
        logger.info("No function calls were made by OpenAI")

    logger.info("📊 Test Summary:")
    logger.info(f"  OpenAI events: {len(openai_parsed)}")
    logger.info(f"  Our events: {len(our_parsed)}")
    logger.info(f"  OpenAI function events: {len(openai_actual_tool_events)}")
    logger.info(f"  Our function events: {len(our_function_events)}")
    compatibility_result = (
        "✅ PASS" if len(our_function_events) > 0 or len(openai_actual_tool_events) == 0 else "❌ FAIL"
    )
    logger.info(f"  Format compatibility: {compatibility_result}")