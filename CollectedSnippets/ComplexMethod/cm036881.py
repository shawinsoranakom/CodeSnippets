async def test_named_tool_use(client: openai.AsyncOpenAI):
    def get_weather(latitude: float, longitude: float) -> str:
        """
        Mock function to simulate getting weather data.
        In a real application, this would call an external weather API.
        """
        return f"Current temperature at ({latitude}, {longitude}) is 20°C."

    tools = [
        {
            "type": "function",
            "name": "get_weather",
            "description": (
                "Get current temperature for provided coordinates in celsius."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "latitude": {"type": "number"},
                    "longitude": {"type": "number"},
                },
                "required": ["latitude", "longitude"],
                "additionalProperties": False,
            },
            "strict": True,
        }
    ]

    input_messages = [
        {"role": "user", "content": "What's the weather like in Paris today?"}
    ]

    response = await client.responses.create(
        model=MODEL_NAME,
        input=input_messages,
        tools=tools,
        tool_choice={"type": "function", "name": "get_weather"},
    )
    assert len(response.output) >= 1
    for out in response.output:
        if out.type == "function_call":
            tool_call = out
    assert tool_call is not None
    assert tool_call.type == "function_call"
    assert tool_call.name == "get_weather"
    args = json.loads(tool_call.arguments)
    assert args["latitude"] is not None
    assert args["longitude"] is not None
    # call the tool
    result = get_weather(args["latitude"], args["longitude"])
    input_messages.append(tool_call)  # append model's function call message
    input_messages.append(
        {  # append result message
            "type": "function_call_output",
            "call_id": tool_call.call_id,
            "output": str(result),
        }
    )
    # create a new response with the tool call result
    response_2 = await client.responses.create(model=MODEL_NAME, input=input_messages)
    # check the output
    assert len(response_2.output_text) > 0