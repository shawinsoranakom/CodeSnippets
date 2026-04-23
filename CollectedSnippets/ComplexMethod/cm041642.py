def render_qwen3_messages(
    processor: Processor,
    messages: list[Message],
    tools: str | None = None,
    is_generate: bool = False,
    enable_thinking: bool = False,
) -> ModelInput:
    """Render messages in the Qwen3 template format.

    See https://huggingface.co/spaces/huggingfacejs/chat-template-playground?modelId=Qwen/Qwen3-8B
    """
    input_ids, labels, loss_weights = [], [], []
    temp_str, temp_weight = "", 0.0
    if tools:
        temp_str += "<|im_start|>system\n"
        if messages[0]["role"] == "system":
            temp_str += _concat_text_content(messages[0]) + "\n\n"
            temp_weight = messages[0].get("loss_weight", 0.0)

        temp_str += (
            "# Tools\n\nYou may call one or more functions to assist with the user query.\n\n"
            "You are provided with function signatures within <tools></tools> XML tags:\n<tools>"
        )
        try:
            tools = json.loads(tools)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid tools format: {str(tools)}.")

        if not isinstance(tools, list):
            tools = [tools]

        for tool in tools:
            temp_str += "\n" + json.dumps(tool, ensure_ascii=False)

        temp_str += (
            "\n</tools>\n\nFor each function call, return a json object with function name "
            'and arguments within <tool_call></tool_call> XML tags:\n<tool_call>\n{"name": '
            '<function-name>, "arguments": <args-json-object>}\n</tool_call><|im_end|>\n'
        )
    elif messages[0]["role"] == "system":
        temp_str += "<|im_start|>system\n" + _concat_text_content(messages[0]) + "<|im_end|>\n"
        temp_weight = messages[0].get("loss_weight", 0.0)

    temp_str = _update_model_input(processor, input_ids, labels, loss_weights, temp_str, temp_weight)
    last_query_index = _get_last_query_index(messages)

    for turn_idx, message in enumerate(messages):
        if message["role"] == "user" or (message["role"] == "system" and turn_idx != 0):
            temp_str += "<|im_start|>" + message["role"] + "\n" + _concat_text_content(message) + "<|im_end|>\n"
            temp_weight = message.get("loss_weight", 0.0)
        elif message["role"] == "assistant":
            temp_str += "<|im_start|>" + message["role"] + "\n"

            text_content, reasoning_content, tool_calls = _split_assistant_content(message)
            if turn_idx > last_query_index and (turn_idx == len(messages) - 1 or reasoning_content):
                temp_str += "<think>\n" + reasoning_content.strip("\n") + "\n</think>\n\n" + text_content.lstrip("\n")
            else:
                temp_str += text_content

            for tool_call_idx, tool_call in enumerate(tool_calls):
                if (tool_call_idx == 0 and text_content) or tool_call_idx > 0:
                    temp_str += "\n"

                arguments = tool_call.get("arguments")
                if isinstance(arguments, str):
                    arguments_str = arguments
                else:
                    arguments_str = json.dumps(arguments, ensure_ascii=False)

                temp_str += (
                    '<tool_call>\n{"name": "'
                    + tool_call["name"]
                    + '", "arguments": '
                    + arguments_str
                    + "}\n</tool_call>"
                )

            temp_str += "<|im_end|>\n"
            temp_weight = message.get("loss_weight", 1.0)
        elif message["role"] == "tool":
            if turn_idx == 0 or messages[turn_idx - 1]["role"] != "tool":
                temp_str += "<|im_start|>user"

            temp_str += "\n<tool_response>\n" + _concat_text_content(message) + "\n</tool_response>"
            if turn_idx == len(messages) - 1 or messages[turn_idx + 1]["role"] != "tool":
                temp_str += "<|im_end|>\n"

            temp_weight = message.get("loss_weight", 0.0)

        temp_str = _update_model_input(processor, input_ids, labels, loss_weights, temp_str, temp_weight)

    if is_generate:
        temp_str += "<|im_start|>assistant\n"
        temp_weight = 0.0
        if enable_thinking is False:
            temp_str += "<think>\n\n</think>\n\n"

    temp_str = _update_model_input(processor, input_ids, labels, loss_weights, temp_str, temp_weight)

    attention_mask = [1] * len(input_ids)
    return ModelInput(
        input_ids=input_ids,
        attention_mask=attention_mask,
        labels=labels,
        loss_weights=loss_weights,
    )