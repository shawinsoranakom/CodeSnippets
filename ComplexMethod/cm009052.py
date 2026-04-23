def after_model(
        self,
        state: ToolCallLimitState[ResponseT],
        runtime: Runtime[ContextT],
    ) -> dict[str, Any] | None:
        """Increment tool call counts after a model call and check limits.

        Args:
            state: The current agent state.
            runtime: The langgraph runtime.

        Returns:
            State updates with incremented tool call counts. If limits are exceeded
                and exit_behavior is `'end'`, also includes a jump to end with a
                `ToolMessage` and AI message for the single exceeded tool call.

        Raises:
            ToolCallLimitExceededError: If limits are exceeded and `exit_behavior`
                is `'error'`.
            NotImplementedError: If limits are exceeded, `exit_behavior` is `'end'`,
                and there are multiple tool calls.
        """
        # Get the last AIMessage to check for tool calls
        messages = state.get("messages", [])
        if not messages:
            return None

        # Find the last AIMessage
        last_ai_message = None
        for message in reversed(messages):
            if isinstance(message, AIMessage):
                last_ai_message = message
                break

        if not last_ai_message or not last_ai_message.tool_calls:
            return None

        # Get the count key for this middleware instance
        count_key = self.tool_name or "__all__"

        # Get current counts
        thread_counts = state.get("thread_tool_call_count", {}).copy()
        run_counts = state.get("run_tool_call_count", {}).copy()
        current_thread_count = thread_counts.get(count_key, 0)
        current_run_count = run_counts.get(count_key, 0)

        # Separate tool calls into allowed and blocked
        allowed_calls, blocked_calls, new_thread_count, new_run_count = self._separate_tool_calls(
            last_ai_message.tool_calls, current_thread_count, current_run_count
        )

        # Update counts to include only allowed calls for thread count
        # (blocked calls don't count towards thread-level tracking)
        # But run count includes blocked calls since they were attempted in this run
        thread_counts[count_key] = new_thread_count
        run_counts[count_key] = new_run_count + len(blocked_calls)

        # If no tool calls are blocked, just update counts
        if not blocked_calls:
            if allowed_calls:
                return {
                    "thread_tool_call_count": thread_counts,
                    "run_tool_call_count": run_counts,
                }
            return None

        # Get final counts for building messages
        final_thread_count = thread_counts[count_key]
        final_run_count = run_counts[count_key]

        # Handle different exit behaviors
        if self.exit_behavior == "error":
            # Use hypothetical thread count to show which limit was exceeded
            hypothetical_thread_count = final_thread_count + len(blocked_calls)
            raise ToolCallLimitExceededError(
                thread_count=hypothetical_thread_count,
                run_count=final_run_count,
                thread_limit=self.thread_limit,
                run_limit=self.run_limit,
                tool_name=self.tool_name,
            )

        # Build tool message content (sent to model - no thread/run details)
        tool_msg_content = _build_tool_message_content(self.tool_name)

        # Inject artificial error ToolMessages for blocked tool calls
        artificial_messages: list[ToolMessage | AIMessage] = [
            ToolMessage(
                content=tool_msg_content,
                tool_call_id=tool_call["id"],
                name=tool_call.get("name"),
                status="error",
            )
            for tool_call in blocked_calls
        ]

        if self.exit_behavior == "end":
            # Check if there are tool calls to other tools that would continue executing
            other_tools = [
                tc
                for tc in last_ai_message.tool_calls
                if self.tool_name is not None and tc["name"] != self.tool_name
            ]

            if other_tools:
                tool_names = ", ".join({tc["name"] for tc in other_tools})
                msg = (
                    f"Cannot end execution with other tool calls pending. "
                    f"Found calls to: {tool_names}. Use 'continue' or 'error' behavior instead."
                )
                raise NotImplementedError(msg)

            # Build final AI message content (displayed to user - includes thread/run details)
            # Use hypothetical thread count (what it would have been if call wasn't blocked)
            # to show which limit was actually exceeded
            hypothetical_thread_count = final_thread_count + len(blocked_calls)
            final_msg_content = _build_final_ai_message_content(
                hypothetical_thread_count,
                final_run_count,
                self.thread_limit,
                self.run_limit,
                self.tool_name,
            )
            artificial_messages.append(AIMessage(content=final_msg_content))

            return {
                "thread_tool_call_count": thread_counts,
                "run_tool_call_count": run_counts,
                "jump_to": "end",
                "messages": artificial_messages,
            }

        # For exit_behavior="continue", return error messages to block exceeded tools
        return {
            "thread_tool_call_count": thread_counts,
            "run_tool_call_count": run_counts,
            "messages": artificial_messages,
        }