def _process_tool_calls(self, result: ChatMessageContent) -> list[FunctionCall]:
        """Process tool calls from SK ChatMessageContent"""
        function_calls: list[FunctionCall] = []
        for item in result.items:
            if isinstance(item, FunctionCallContent):
                # Extract plugin name and function name
                plugin_name = item.plugin_name or ""
                function_name = item.function_name
                if plugin_name:
                    full_name = f"{plugin_name}-{function_name}"
                else:
                    full_name = function_name

                if item.id is None:
                    raise ValueError("Function call ID is required")

                if isinstance(item.arguments, Mapping):
                    arguments = json.dumps(item.arguments)
                else:
                    arguments = item.arguments or "{}"

                function_calls.append(FunctionCall(id=item.id, name=full_name, arguments=arguments))
        return function_calls