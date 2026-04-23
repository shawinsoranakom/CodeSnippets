def to_openai_messages(self) -> list[ChatCompletionMessageParam]:
        messages = []
        for message in self.messages:
            if message.role == "developer":
                m = ChatCompletionDeveloperMessageParam(
                    role="developer",
                    content=message.content or "",
                )
                if message.name:
                    m["name"] = message.name
                messages.append(m)
            elif message.role == "system":
                m = ChatCompletionSystemMessageParam(
                    role="system",
                    content=message.content or "",
                )
                if message.name:
                    m["name"] = message.name
                messages.append(m)
            elif message.role == "user":
                m = ChatCompletionUserMessageParam(
                    role="user",
                    content=message.content or "",
                )
                if message.name:
                    m["name"] = message.name
                messages.append(m)
            elif message.role == "assistant":
                m = ChatCompletionAssistantMessageParam(
                    role="assistant",
                    content=message.content or "",
                )
                if message.function_call:
                    m["function_call"] = FunctionCall(
                        arguments=message.function_call["arguments"],
                        name=message.function_call["name"],
                    )
                if message.refusal:
                    m["refusal"] = message.refusal
                if message.tool_calls:
                    t: list[ChatCompletionMessageToolCallParam] = []
                    for tool_call in message.tool_calls:
                        # Tool calls are stored with nested structure: {id, type, function: {name, arguments}}
                        function_data = tool_call.get("function", {})

                        # Skip tool calls that are missing required fields
                        if "id" not in tool_call or "name" not in function_data:
                            logger.warning(
                                f"Skipping invalid tool call: missing required fields. "
                                f"Got: {tool_call.keys()}, function keys: {function_data.keys()}"
                            )
                            continue

                        # Arguments are stored as a JSON string
                        arguments_str = function_data.get("arguments", "{}")

                        t.append(
                            ChatCompletionMessageToolCallParam(
                                id=tool_call["id"],
                                type="function",
                                function=Function(
                                    arguments=arguments_str,
                                    name=function_data["name"],
                                ),
                            )
                        )
                    m["tool_calls"] = t
                if message.name:
                    m["name"] = message.name
                messages.append(m)
            elif message.role == "tool":
                messages.append(
                    ChatCompletionToolMessageParam(
                        role="tool",
                        content=message.content or "",
                        tool_call_id=message.tool_call_id or "",
                    )
                )
            elif message.role == "function":
                messages.append(
                    ChatCompletionFunctionMessageParam(
                        role="function",
                        content=message.content,
                        name=message.name or "",
                    )
                )
        return self._merge_consecutive_assistant_messages(messages)