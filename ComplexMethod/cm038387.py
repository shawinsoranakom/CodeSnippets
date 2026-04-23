def extract_tool_calls(
        self,
        model_output: str,
        request: ChatCompletionRequest,
    ) -> ExtractedToolCallInformation:
        """
        Extract the tool calls from a complete model response.

        Content and tool calls formatting depends on the Mistral's tokenizer version
        used to train the model:

        - < v11: `content[BOT] [{tool_call1},{tool_call2}]`
        - >= v11: `content[BOT]tool_name1{args_call1}[BOT]tool_name2{args_call2}`

        with [BOT] the tool call token.

        Note:
            For tokenizer versions >= v11, tool calls with arguments wrongly formatted
            are still returned as tool calls. This is to allow the model to know it
            tried to make a tool call. It reduces chance of another failure and
            prevents that the context is filled with tool calls wrongly placed in
            assistant message contents.
        """

        # If the tool call token is not present, return a text response
        if self.bot_token not in model_output:
            return ExtractedToolCallInformation(
                tools_called=False, tool_calls=[], content=model_output
            )

        content_and_raw_tool_calls = model_output.split(self.bot_token)
        content = content_and_raw_tool_calls[0]
        raw_tool_calls = content_and_raw_tool_calls[1:]

        # >= v11: content[BOT]tool_name1{args_call1}[BOT]tool_name2{args_call2}
        if not self._is_pre_v11:
            tool_calls = []
            for raw_tool_call in raw_tool_calls:
                if "{" not in raw_tool_call:
                    continue

                end_name = raw_tool_call.find("{")
                tool_name, args = (
                    raw_tool_call[:end_name],
                    raw_tool_call[end_name:],
                )

                tool_calls.append({"name": tool_name, "arguments": args})

        # < v11: content[BOT] [{tool_call1},{tool_call2}]
        else:
            if len(raw_tool_calls) != 1:
                raise ValueError(
                    "Only one BOT token should have been outputted, "
                    f"but got {model_output}."
                )
            stringified_tool_calls = raw_tool_calls[0].strip()
            try:
                # Use raw_decode to parse the first valid JSON value,
                # ignoring trailing tokens the model may emit after
                # the tool call array.
                tool_calls, _ = json.JSONDecoder().raw_decode(stringified_tool_calls)
            except json.JSONDecodeError:
                try:
                    raw_tool_call = self.tool_call_regex.findall(
                        stringified_tool_calls
                    )[0]
                    tool_calls = json.loads(raw_tool_call)
                    tool_calls = [
                        {
                            "name": tool_call["name"],
                            "arguments": json.dumps(
                                tool_call.get("arguments", {}),
                                ensure_ascii=False,
                            ),
                        }
                        for tool_call in tool_calls
                    ]
                except (IndexError, json.JSONDecodeError):
                    logger.exception("Error in extracting tool call from response.")
                    return ExtractedToolCallInformation(
                        tools_called=False,
                        tool_calls=[],
                        content=stringified_tool_calls,
                    )
            else:
                tool_calls = [
                    {
                        "name": tool_call["name"],
                        "arguments": json.dumps(
                            tool_call.get("arguments", {}),
                            ensure_ascii=False,
                        ),
                    }
                    for tool_call in tool_calls
                ]

        mistral_tool_calls: list[MistralToolCall] = [
            MistralToolCall(
                type="function",
                function=FunctionCall(
                    name=tool_call["name"],
                    arguments=tool_call.get("arguments", "{}"),
                ),
            )
            for tool_call in tool_calls
        ]

        return ExtractedToolCallInformation(
            tools_called=True,
            tool_calls=mistral_tool_calls,
            content=content if len(content) > 0 else None,
        )