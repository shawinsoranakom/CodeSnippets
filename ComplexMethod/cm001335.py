def _process_latest_result_from_messages(self, messages: list[ChatMessage]) -> None:
        """Extract and process the latest execution result from message history.

        The ActionHistoryComponent includes tool results in the messages.
        We look for the most recent tool result to process for reflection.
        This is called at the start of build_prompt() to ensure results are
        processed before building the next prompt.

        This enables Reflexion to work without requiring changes to agent.py -
        the strategy self-extracts results from the standard message flow.
        """
        if not self.last_action:
            # No action recorded yet, nothing to process
            return

        # Look for tool result messages (from ActionHistoryComponent)
        for msg in reversed(messages):
            content = None
            is_error = False

            # Check for ToolResultMessage (has tool_call_id attribute)
            if hasattr(msg, "tool_call_id") and hasattr(msg, "content"):
                content = msg.content
                is_error = getattr(msg, "is_error", False)
            # Also check for user messages that contain result format
            elif hasattr(msg, "role") and getattr(msg, "role", None) == "user":
                msg_content = getattr(msg, "content", str(msg))
                if isinstance(msg_content, str):
                    if (
                        " returned:" in msg_content
                        or " raised an error:" in msg_content
                    ):
                        content = msg_content
                        is_error = " raised an error:" in msg_content

            if content is not None:
                # Only process if we haven't already processed this result
                if self.last_result is None or self.last_result != content:
                    self.logger.debug(
                        f"Reflexion: Extracted result from messages (error={is_error})"
                    )
                    self.record_result(content, success=not is_error)
                return