def _convert_to_chat_history(self, messages: Sequence[LLMMessage]) -> ChatHistory:
        """Convert Autogen LLMMessages to SK ChatHistory"""
        chat_history = ChatHistory()

        for msg in messages:
            if msg.type == "SystemMessage":
                chat_history.add_system_message(msg.content)

            elif msg.type == "UserMessage":
                if isinstance(msg.content, str):
                    chat_history.add_user_message(msg.content)
                else:
                    # Handle list of str/Image - convert to string for now
                    chat_history.add_user_message(str(msg.content))

            elif msg.type == "AssistantMessage":
                # Check if it's a function-call style message
                if isinstance(msg.content, list) and all(isinstance(fc, FunctionCall) for fc in msg.content):
                    # If there's a 'thought' field, you can add that as plain assistant text
                    if msg.thought:
                        chat_history.add_assistant_message(msg.thought)

                    function_call_contents: list[FunctionCallContent] = []
                    for fc in msg.content:
                        function_call_contents.append(
                            FunctionCallContent(
                                id=fc.id,
                                name=fc.name,
                                plugin_name=self._tools_plugin.name,
                                function_name=fc.name,
                                arguments=fc.arguments,
                            )
                        )

                    # Mark the assistant's message as tool-calling
                    chat_history.add_assistant_message(
                        function_call_contents,
                        finish_reason=FinishReason.TOOL_CALLS,
                    )
                else:
                    # Plain assistant text
                    chat_history.add_assistant_message(msg.content)

            elif msg.type == "FunctionExecutionResultMessage":
                # Add each function result as a separate tool message
                tool_results: list[FunctionResultContent] = []
                for result in msg.content:
                    tool_results.append(
                        FunctionResultContent(
                            id=result.call_id,
                            plugin_name=self._tools_plugin.name,
                            function_name=result.name,
                            result=result.content,
                        )
                    )
                # A single "tool" message with one or more results
                chat_history.add_tool_message(tool_results)

        return chat_history