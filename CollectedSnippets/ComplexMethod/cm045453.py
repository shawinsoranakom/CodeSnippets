def _check_and_handle_handoff(
        model_result: CreateResult,
        executed_calls_and_results: List[Tuple[FunctionCall, FunctionExecutionResult]],
        inner_messages: List[BaseAgentEvent | BaseChatMessage],
        handoffs: Dict[str, HandoffBase],
        agent_name: str,
    ) -> Optional[Response]:
        """Check for and handle any handoff requests in the model result.

        Args:
            model_result: Result from model inference
            executed_calls_and_results: List of executed tool calls and their results
            inner_messages: List of messages generated during processing
            handoffs: Dictionary of available handoff configurations
            agent_name: Name of the agent

        Returns:
            Optional response containing handoff message if handoff detected
        """
        handoff_reqs = [
            call for call in model_result.content if isinstance(call, FunctionCall) and call.name in handoffs
        ]
        if len(handoff_reqs) > 0:
            # We have at least one handoff function call
            selected_handoff = handoffs[handoff_reqs[0].name]

            if len(handoff_reqs) > 1:
                warnings.warn(
                    (
                        f"Multiple handoffs detected. Only the first is executed: "
                        f"{[handoffs[c.name].name for c in handoff_reqs]}. "
                        "Disable parallel tool calls in the model client to avoid this warning."
                    ),
                    stacklevel=2,
                )

            # Collect normal tool calls (not handoff) into the handoff context
            tool_calls: List[FunctionCall] = []
            tool_call_results: List[FunctionExecutionResult] = []
            # Collect the results returned by handoff_tool. By default, the message attribute will returned.
            selected_handoff_message = selected_handoff.message
            for exec_call, exec_result in executed_calls_and_results:
                if exec_call.name not in handoffs:
                    tool_calls.append(exec_call)
                    tool_call_results.append(exec_result)
                elif exec_call.name == selected_handoff.name:
                    selected_handoff_message = exec_result.content

            handoff_context: List[LLMMessage] = []
            if len(tool_calls) > 0:
                # Include the thought in the AssistantMessage if model_result has it
                handoff_context.append(
                    AssistantMessage(
                        content=tool_calls,
                        source=agent_name,
                        thought=getattr(model_result, "thought", None),
                    )
                )
                handoff_context.append(FunctionExecutionResultMessage(content=tool_call_results))
            elif model_result.thought:
                # If no tool calls, but a thought exists, include it in the context
                handoff_context.append(
                    AssistantMessage(
                        content=model_result.thought,
                        source=agent_name,
                    )
                )

            # Return response for the first handoff
            return Response(
                chat_message=HandoffMessage(
                    content=selected_handoff_message,
                    target=selected_handoff.target,
                    source=agent_name,
                    context=handoff_context,
                ),
                inner_messages=inner_messages,
            )
        return None