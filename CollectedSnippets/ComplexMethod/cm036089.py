def test_streaming_output_valid(output, empty_params, delta_len):
    self = MagicMock()

    output = deepcopy(output)
    if empty_params:
        output = [{"name": o["name"], "parameters": {}} for o in output]
    output_json = json.dumps(output)

    previous_text = ""
    function_name_returned = False
    messages = []
    for i in range(0, len(output_json), delta_len):
        delta_text = output_json[i : i + delta_len]
        current_text = previous_text + delta_text

        delta_message, function_name_returned = (
            OpenAIServingChat.extract_tool_call_required_streaming(
                self,
                previous_text=previous_text,
                current_text=current_text,
                delta_text=delta_text,
                function_name_returned=function_name_returned,
            )
        )

        if delta_message:
            messages.append(delta_message)

        previous_text = current_text

    assert len(messages) > 0

    combined_messages = "["
    for message in messages:
        if message.tool_calls[0].function.name:
            if len(combined_messages) > 1:
                combined_messages += "},"

            combined_messages += (
                '{"name": "'
                + message.tool_calls[0].function.name
                + '", "parameters": '
                + message.tool_calls[0].function.arguments
            )
        else:
            combined_messages += message.tool_calls[0].function.arguments
    combined_messages += "}]"
    assert json.loads(combined_messages) == output
    assert json.dumps(json.loads(combined_messages)) == output_json