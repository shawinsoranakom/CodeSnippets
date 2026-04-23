def after_model(
        self, state: AgentState[Any], runtime: Runtime[ContextT]
    ) -> dict[str, Any] | None:
        """Trigger interrupt flows for relevant tool calls after an `AIMessage`.

        Args:
            state: The current agent state.
            runtime: The runtime context.

        Returns:
            Updated message with the revised tool calls.

        Raises:
            ValueError: If the number of human decisions does not match the number of
                interrupted tool calls.
        """
        messages = state["messages"]
        if not messages:
            return None

        last_ai_msg = next((msg for msg in reversed(messages) if isinstance(msg, AIMessage)), None)
        if not last_ai_msg or not last_ai_msg.tool_calls:
            return None

        # Create action requests and review configs for tools that need approval
        action_requests: list[ActionRequest] = []
        review_configs: list[ReviewConfig] = []
        interrupt_indices: list[int] = []

        for idx, tool_call in enumerate(last_ai_msg.tool_calls):
            if (config := self.interrupt_on.get(tool_call["name"])) is not None:
                action_request, review_config = self._create_action_and_config(
                    tool_call, config, state, runtime
                )
                action_requests.append(action_request)
                review_configs.append(review_config)
                interrupt_indices.append(idx)

        # If no interrupts needed, return early
        if not action_requests:
            return None

        # Create single HITLRequest with all actions and configs
        hitl_request = HITLRequest(
            action_requests=action_requests,
            review_configs=review_configs,
        )

        # Send interrupt and get response
        decisions = interrupt(hitl_request)["decisions"]

        # Validate that the number of decisions matches the number of interrupt tool calls
        if (decisions_len := len(decisions)) != (interrupt_count := len(interrupt_indices)):
            msg = (
                f"Number of human decisions ({decisions_len}) does not match "
                f"number of hanging tool calls ({interrupt_count})."
            )
            raise ValueError(msg)

        # Process decisions and rebuild tool calls in original order
        revised_tool_calls: list[ToolCall] = []
        artificial_tool_messages: list[ToolMessage] = []
        decision_idx = 0

        for idx, tool_call in enumerate(last_ai_msg.tool_calls):
            if idx in interrupt_indices:
                # This was an interrupt tool call - process the decision
                config = self.interrupt_on[tool_call["name"]]
                decision = decisions[decision_idx]
                decision_idx += 1

                revised_tool_call, tool_message = self._process_decision(
                    decision, tool_call, config
                )
                if revised_tool_call is not None:
                    revised_tool_calls.append(revised_tool_call)
                if tool_message:
                    artificial_tool_messages.append(tool_message)
            else:
                # This was auto-approved - keep original
                revised_tool_calls.append(tool_call)

        # Update the AI message to only include approved tool calls
        last_ai_msg.tool_calls = revised_tool_calls

        return {"messages": [last_ai_msg, *artificial_tool_messages]}