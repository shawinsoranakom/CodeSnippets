def process(self, output: CompletionOutput) -> "ResponsesParser":
        # Store the finish_reason from the output
        self.finish_reason = output.finish_reason

        reasoning, content = self.reasoning_parser_instance.extract_reasoning(
            output.text, request=self.request
        )
        if reasoning:
            self.response_messages.append(
                ResponseReasoningItem(
                    type="reasoning",
                    id=f"rs_{random_uuid()}",
                    summary=[],
                    content=[
                        Content(
                            type="reasoning_text",
                            text=reasoning,
                        )
                    ],
                )
            )

        function_calls: list[ResponseFunctionToolCall] = []
        if self.tool_parser_instance is not None:
            tool_call_info = self.tool_parser_instance.extract_tool_calls(
                content if content is not None else "",
                request=self.request,  # type: ignore
            )
            if tool_call_info is not None and tool_call_info.tools_called:
                # extract_tool_calls() returns a list of tool calls.
                function_calls.extend(
                    ResponseFunctionToolCall(
                        id=f"fc_{random_uuid()}",
                        call_id=f"call_{random_uuid()}",
                        type="function_call",
                        status="completed",
                        name=tool_call.function.name,
                        arguments=tool_call.function.arguments,
                    )
                    for tool_call in tool_call_info.tool_calls
                )
                content = tool_call_info.content
                if content and content.strip() == "":
                    content = None

        if content:
            self.response_messages.append(
                ResponseOutputMessage(
                    type="message",
                    id=f"msg_{random_uuid()}",
                    status="completed",
                    role="assistant",
                    content=[
                        ResponseOutputText(
                            annotations=[],  # TODO
                            type="output_text",
                            text=content,
                            logprobs=None,  # TODO
                        )
                    ],
                )
            )
        if len(function_calls) > 0:
            self.response_messages.extend(function_calls)

        return self