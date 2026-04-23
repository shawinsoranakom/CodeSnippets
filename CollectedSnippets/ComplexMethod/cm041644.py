def render_qwen3_nothink_messages(
    processor: Processor,
    messages: list[Message],
    tools: str | None = None,
    is_generate: bool = False,
    enable_thinking: bool = False,
) -> ModelInput:
    """Render messages in the Qwen3 nothink template format.

    See https://huggingface.co/spaces/huggingfacejs/chat-template-playground?modelId=Qwen/Qwen3-4B-Instruct-2507
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

    for turn_idx, message in enumerate(messages):
        if message["role"] == "user" or (message["role"] == "system" and turn_idx != 0):
            temp_str += "<|im_start|>" + message["role"] + "\n" + _concat_text_content(message) + "<|im_end|>\n"
            temp_weight = message.get("loss_weight", 0.0)
        elif message["role"] == "assistant":
            temp_str += "<|im_start|>" + message["role"] + "\n"
            for val_idx, content in enumerate(message["content"]):
                if content["type"] == "text":
                    temp_str += content["value"]
                elif content["type"] == "reasoning":
                    temp_str += "<thinking>\n" + content["value"] + "\n</thinking>\n\n"  # avoid using special tokens
                elif content["type"] == "tool_call":
                    if val_idx != 0 and message["content"][val_idx - 1]["type"] in ["text", "tool_call"]:
                        temp_str += "\n"

                    try:
                        tool_call: ToolCall = json.loads(content["value"])
                    except json.JSONDecodeError:
                        raise ValueError(f"Invalid tool call format: {content['value']}.")

                    temp_str += (
                        '<tool_call>\n{"name": "'
                        + tool_call["name"]
                        + '", "arguments": '
                        + json.dumps(tool_call["arguments"], ensure_ascii=False)
                        + "}\n</tool_call>"
                    )

                else:
                    raise ValueError(f"Unsupported content type: {content['type']}")

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
        if enable_thinking:
            raise ValueError("The qwen3_nothink template does not support thinking mode.")

    temp_str = _update_model_input(processor, input_ids, labels, loss_weights, temp_str, temp_weight)

    attention_mask = [1] * len(input_ids)
    return ModelInput(
        input_ids=input_ids,
        attention_mask=attention_mask,
        labels=labels,
        loss_weights=loss_weights,
    )