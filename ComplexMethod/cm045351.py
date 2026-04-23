async def call_tool_stream(
        self,
        name: str,
        arguments: Mapping[str, Any] | None = None,
        cancellation_token: CancellationToken | None = None,
        call_id: str | None = None,
    ) -> AsyncGenerator[Any | ToolResult, None]:
        tool = next((tool for tool in self._tools if tool.name == name), None)
        if tool is None:
            yield ToolResult(
                name=name,
                result=[TextResultContent(content=f"Tool {name} not found.")],
                is_error=True,
            )
            return
        if not cancellation_token:
            cancellation_token = CancellationToken()
        if not arguments:
            arguments = {}
        try:
            actual_tool_output: Any | None = None
            if isinstance(tool, StreamTool):
                previous_result: Any | None = None
                try:
                    async for result in tool.run_json_stream(arguments, cancellation_token, call_id=call_id):
                        if previous_result is not None:
                            yield previous_result
                        previous_result = result
                    actual_tool_output = previous_result
                except Exception as e:
                    # If there was a previous result before the exception, yield it first
                    if previous_result is not None:
                        yield previous_result
                    # Then yield the error result
                    result_str = self._format_errors(e)
                    yield ToolResult(name=tool.name, result=[TextResultContent(content=result_str)], is_error=True)
                    return
            else:
                # If the tool is not a stream tool, we run it normally and yield the result
                result_future = asyncio.ensure_future(tool.run_json(arguments, cancellation_token, call_id=call_id))
                cancellation_token.link_future(result_future)
                actual_tool_output = await result_future
            is_error = False
            result_str = tool.return_value_as_string(actual_tool_output)
        except Exception as e:
            result_str = self._format_errors(e)
            is_error = True
        yield ToolResult(name=tool.name, result=[TextResultContent(content=result_str)], is_error=is_error)