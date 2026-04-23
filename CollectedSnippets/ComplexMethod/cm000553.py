async def _agent_mode_tool_executor(
        self,
        tool_call: LLMToolCall,
        tools: Sequence[Any],
        *,
        execution_params: ExecutionParams,
        execution_processor: "ExecutionProcessor",
        use_responses_api: bool,
    ) -> ToolCallResult:
        """Tool executor callback for agent mode: wraps _execute_single_tool_with_manager."""
        # Find tool definition
        tool_def = next(
            (t for t in tools if t["function"]["name"] == tool_call.name),
            None,
        )
        if not tool_def and len(tools) == 1:
            tool_def = tools[0]
        if not tool_def:
            return ToolCallResult(
                tool_call_id=tool_call.id,
                tool_name=tool_call.name,
                content=f"Unknown tool: {tool_call.name}",
                is_error=True,
            )

        try:
            tool_args = json.loads(tool_call.arguments)
        except (ValueError, TypeError) as e:
            return ToolCallResult(
                tool_call_id=tool_call.id,
                tool_name=tool_call.name,
                content=f"Invalid JSON arguments: {e}",
                is_error=True,
            )
        tool_info = OrchestratorBlock._build_tool_info_from_args(
            tool_call_id=tool_call.id,
            tool_name=tool_call.name,
            tool_args=tool_args,
            tool_def=tool_def,
        )

        try:
            result = await self._execute_single_tool_with_manager(
                tool_info,
                execution_params,
                execution_processor,
                responses_api=use_responses_api,
            )
            # Unwrap the tool content from the provider-specific envelope.
            # _execute_single_tool_with_manager returns a full message dict
            # (e.g. {"role":"tool","content":"..."} for Chat API,
            #  or {"type":"function_call_output","output":"..."} for Responses API).
            raw_content = result.get("content") or result.get("output")
            if isinstance(raw_content, list):
                # Anthropic format: [{"type":"tool_result","content":"..."}]
                parts = [
                    item.get("content", "")
                    for item in raw_content
                    if isinstance(item, dict)
                ]
                content = (
                    "\n".join(str(p) for p in parts)
                    if parts
                    else "Tool executed successfully"
                )
            elif raw_content is not None:
                content = str(raw_content)
            else:
                content = "Tool executed successfully"
            tool_failed = result.get("_is_error", True)
            return ToolCallResult(
                tool_call_id=tool_call.id,
                tool_name=tool_call.name,
                content=content,
                is_error=tool_failed,
            )
        except InsufficientBalanceError:
            # IBE must propagate — see class docstring.
            raise
        except Exception as e:
            logger.error("Tool execution failed: %s", e)
            return ToolCallResult(
                tool_call_id=tool_call.id,
                tool_name=tool_call.name,
                content=f"Error: {e}",
                is_error=True,
            )