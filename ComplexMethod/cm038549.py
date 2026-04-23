def render_message(
    index: int, messages: list[dict[str, Any]], thinking_mode: str
) -> str:
    if not (0 <= index < len(messages)):
        raise ValueError(
            f"Index {index} out of range for messages list of length {len(messages)}"
        )
    if thinking_mode not in ["chat", "thinking"]:
        raise ValueError(f"Invalid thinking_mode `{thinking_mode}`")

    prompt = ""
    msg = messages[index]
    last_user_idx = find_last_user_index(messages)

    role = msg.get("role")
    content = msg.get("content")
    tools = msg.get("tools")
    response_format = msg.get("response_format")
    tool_calls = msg.get("tool_calls")
    reasoning = msg.get("reasoning")
    is_prefix = msg.get("prefix", False)

    if tools:
        tools = tools_from_openai_format(tools)
    if tool_calls:
        tool_calls = tool_calls_from_openai_format(tool_calls)

    if role == "system":
        prompt += system_msg_template.format(content=content or "")
        if tools:
            prompt += "\n\n" + render_tools(tools)

        if response_format:
            prompt += "\n\n" + response_format_template.format(
                schema=to_json(response_format)
            )

    elif role == "developer":
        if not content:
            raise ValueError(f"Invalid message for role `{role}`: {msg}")
        content_developer = ""
        if tools:
            content_developer += "\n\n" + render_tools(tools)

        if response_format:
            content_developer += "\n\n" + response_format_template.format(
                schema=to_json(response_format)
            )

        content_developer += "\n\n# The user's message is: {}".format(content)

        prompt += user_msg_template.format(content=content_developer)
        if index == last_user_idx and thinking_mode == "thinking":
            prompt += thinking_start_token
        else:
            prompt += thinking_end_token

    elif role == "user":
        prompt += user_msg_template.format(content=content)

        if index == last_user_idx and thinking_mode == "thinking":
            prompt += thinking_start_token
        else:
            prompt += thinking_end_token

    elif role == "tool":
        prev_assistant_idx = index - 1
        assistant_msg = messages[prev_assistant_idx]
        while prev_assistant_idx >= 0 and assistant_msg.get("role") == "tool":
            prev_assistant_idx -= 1
            assistant_msg = messages[prev_assistant_idx]

        if not (
            index == 0
            or prev_assistant_idx >= 0
            and assistant_msg.get("role") == "assistant"
        ):
            raise ValueError(f"Invalid messages at {index}:\n{assistant_msg}")

        tool_call_order = index - prev_assistant_idx
        assistant_tool_calls = assistant_msg.get("tool_calls")
        if not (assistant_tool_calls and len(assistant_tool_calls) >= tool_call_order):
            raise ValueError("No tool calls but found tool output")

        if tool_call_order == 1:
            prompt += "\n\n<function_results>"

        prompt += tool_output_template.format(content=content)

        if tool_call_order == len(assistant_tool_calls):
            prompt += "\n</function_results>"

            if index >= last_user_idx and thinking_mode == "thinking":
                prompt += "\n\n" + thinking_start_token
            else:
                prompt += "\n\n" + thinking_end_token

    elif role == "assistant":
        prev_assistant_idx = index
        thinking_part = ""

        tool_calls_content = ""
        if tool_calls:
            tool_calls = [
                tool_call_template.format(
                    dsml_token=dsml_token,
                    name=tool_call.get("name"),
                    arguments=encode_arguments_to_dsml(tool_call),
                )
                for tool_call in tool_calls
            ]
            tool_calls_content += "\n\n" + tool_calls_template.format(
                dsml_token=dsml_token, tool_calls="\n".join(tool_calls)
            )

        summary_content = content or ""

        if thinking_mode == "thinking" and index > last_user_idx:
            if not (reasoning or tool_calls):
                raise ValueError(
                    f"ThinkingMode: {thinking_mode}, invalid message without reasoning/tool_calls `{msg}` after last user message"
                )
            thinking_part = (
                thinking_template.format(reasoning=reasoning or "") + thinking_end_token
            )

        if not tool_calls and is_prefix:
            prompt += summary_content
        else:
            prompt += assistant_msg_template.format(
                reasoning=thinking_part,
                content=summary_content,
                tool_calls=tool_calls_content,
            )
    else:
        raise NotImplementedError(f"Unknown role: {role}")

    return prompt