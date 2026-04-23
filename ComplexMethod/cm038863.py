def process_stream(response, tool_functions, original_query):
    """Process a streaming response with possible tool calls"""
    # Track multiple tool calls
    tool_calls = {}  # Dictionary to store tool calls by ID

    current_id = None

    print("\n--- Stream Output ---")
    for chunk in response:
        # Handle tool calls in the stream
        if chunk.choices[0].delta.tool_calls:
            for tool_call_chunk in chunk.choices[0].delta.tool_calls:
                # Get the tool call ID
                if hasattr(tool_call_chunk, "id") and tool_call_chunk.id:
                    current_id = tool_call_chunk.id
                    if current_id not in tool_calls:
                        tool_calls[current_id] = {
                            "function_name": None,
                            "function_args": "",
                            "function_id": current_id,
                        }

                # Extract function information as it comes in chunks
                if (
                    hasattr(tool_call_chunk, "function")
                    and current_id
                    and current_id in tool_calls
                ):
                    if (
                        hasattr(tool_call_chunk.function, "name")
                        and tool_call_chunk.function.name
                    ):
                        tool_calls[current_id]["function_name"] = (
                            tool_call_chunk.function.name
                        )
                        print(f"Function called: {tool_call_chunk.function.name}")

                    if (
                        hasattr(tool_call_chunk.function, "arguments")
                        and tool_call_chunk.function.arguments
                    ):
                        tool_calls[current_id]["function_args"] += (
                            tool_call_chunk.function.arguments
                        )
                        print(f"Arguments chunk: {tool_call_chunk.function.arguments}")

        # Handle regular content in the stream
        elif chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="")

    print("\n--- End Stream ---\n")

    # Execute each function call and build messages for follow-up
    follow_up_messages = [{"role": "user", "content": original_query}]

    for tool_id, tool_data in tool_calls.items():
        function_name = tool_data["function_name"]
        function_args = tool_data["function_args"]
        function_id = tool_data["function_id"]

        if function_name and function_args:
            try:
                # Parse the JSON arguments
                args = json.loads(function_args)

                # Call the function with the arguments
                function_result = tool_functions[function_name](**args)
                print(
                    f"\n--- Function Result ({function_name}) ---\n{function_result}\n"
                )

                # Add the assistant message with tool call
                follow_up_messages.append(
                    {
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "id": function_id,
                                "type": "function",
                                "function": {
                                    "name": function_name,
                                    "arguments": function_args,
                                },
                            }
                        ],
                    }
                )

                # Add the tool message with function result
                follow_up_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": function_id,
                        "content": function_result,
                    }
                )

            except Exception as e:
                print(f"Error executing function: {e}")

    # Only send follow-up if we have results to process
    if len(follow_up_messages) > 1:
        # Create a follow-up message with all the function results
        follow_up_response = client.chat.completions.create(
            model=client.models.list().data[0].id,
            messages=follow_up_messages,
            stream=True,
        )

        print("\n--- Follow-up Response ---")
        for chunk in follow_up_response:
            if chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="")
        print("\n--- End Follow-up ---\n")