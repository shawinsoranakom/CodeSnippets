async def _execute_tool_call(
        tool_call: FunctionCall,
        workbench: Sequence[Workbench],
        handoff_tools: List[BaseTool[Any, Any]],
        agent_name: str,
        cancellation_token: CancellationToken,
        stream: asyncio.Queue[BaseAgentEvent | BaseChatMessage | None],
    ) -> Tuple[FunctionCall, FunctionExecutionResult]:
        """Execute a single tool call and return the result."""
        # Load the arguments from the tool call.
        try:
            arguments = json.loads(tool_call.arguments)
        except json.JSONDecodeError as e:
            return (
                tool_call,
                FunctionExecutionResult(
                    content=f"Error: {e}",
                    call_id=tool_call.id,
                    is_error=True,
                    name=tool_call.name,
                ),
            )

        # Check if the tool call is a handoff.
        # TODO: consider creating a combined workbench to handle both handoff and normal tools.
        for handoff_tool in handoff_tools:
            if tool_call.name == handoff_tool.name:
                # Run handoff tool call.
                result = await handoff_tool.run_json(arguments, cancellation_token, call_id=tool_call.id)
                result_as_str = handoff_tool.return_value_as_string(result)
                return (
                    tool_call,
                    FunctionExecutionResult(
                        content=result_as_str,
                        call_id=tool_call.id,
                        is_error=False,
                        name=tool_call.name,
                    ),
                )

        # Handle normal tool call using workbench.
        for wb in workbench:
            tools = await wb.list_tools()
            if any(t["name"] == tool_call.name for t in tools):
                if isinstance(wb, StaticStreamWorkbench):
                    tool_result: ToolResult | None = None
                    async for event in wb.call_tool_stream(
                        name=tool_call.name,
                        arguments=arguments,
                        cancellation_token=cancellation_token,
                        call_id=tool_call.id,
                    ):
                        if isinstance(event, ToolResult):
                            tool_result = event
                        elif isinstance(event, BaseAgentEvent) or isinstance(event, BaseChatMessage):
                            await stream.put(event)
                        else:
                            warnings.warn(
                                f"Unexpected event type: {type(event)} in tool call streaming.",
                                UserWarning,
                                stacklevel=2,
                            )
                    assert isinstance(tool_result, ToolResult), "Tool result should not be None in streaming mode."
                else:
                    tool_result = await wb.call_tool(
                        name=tool_call.name,
                        arguments=arguments,
                        cancellation_token=cancellation_token,
                        call_id=tool_call.id,
                    )
                return (
                    tool_call,
                    FunctionExecutionResult(
                        content=tool_result.to_text(),
                        call_id=tool_call.id,
                        is_error=tool_result.is_error,
                        name=tool_call.name,
                    ),
                )

        return (
            tool_call,
            FunctionExecutionResult(
                content=f"Error: tool '{tool_call.name}' not found in any workbench",
                call_id=tool_call.id,
                is_error=True,
                name=tool_call.name,
            ),
        )