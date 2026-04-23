async def message_response(self) -> Message:
        """Generate a message response using the Cuga agent.

        This method processes the input through the Cuga agent and returns a structured
        message response. It handles agent initialization, tool setup, and event processing.

        Returns:
            Message: The agent's response message

        Raises:
            Exception: If there's an error during agent execution
        """
        logger.debug("[CUGA] Starting Cuga agent run for message_response.")
        logger.debug(f"[CUGA] Agent input value: {self.input_value}")

        # Validate input is not empty
        if not self.input_value or not str(self.input_value).strip():
            msg = "Message cannot be empty. Please provide a valid message."
            raise ValueError(msg)

        try:
            from lfx.schema.content_block import ContentBlock
            from lfx.schema.message import MESSAGE_SENDER_AI

            llm_model, self.chat_history, self.tools = await self.get_agent_requirements()

            # Create agent message for event processing
            agent_message = Message(
                sender=MESSAGE_SENDER_AI,
                sender_name="Cuga",
                properties={"icon": "Bot", "state": "partial"},
                content_blocks=[ContentBlock(title="Agent Steps", contents=[])],
                session_id=self.graph.session_id,
            )

            # Pre-assign an ID for event processing, following the base agent pattern
            # This ensures streaming works even when not connected to ChatOutput
            if not self.is_connected_to_chat_output():
                # When not connected to ChatOutput, assign ID upfront for streaming support
                agent_message.data["id"] = uuid.uuid4()

            # Get input text
            input_text = self.input_value.text if hasattr(self.input_value, "text") else str(self.input_value)

            # Create event iterator from call_agent
            event_iterator = self.call_agent(
                current_input=input_text, tools=self.tools or [], history_messages=self.chat_history, llm=llm_model
            )

            # Process events using the existing event processing system
            from lfx.base.agents.events import process_agent_events

            # Create a wrapper that forces DB updates for event handlers
            # This ensures the UI can see loading steps in real-time via polling
            async def force_db_update_send_message(message, id_=None, *, skip_db_update=False):  # noqa: ARG001
                # Always persist to DB so polling-based UI shows loading steps in real-time
                content_blocks_len = len(message.content_blocks[0].contents) if message.content_blocks else 0
                logger.debug(
                    f"[CUGA] Sending message update - state: {message.properties.state}, "
                    f"content_blocks: {content_blocks_len}"
                )

                result = await self.send_message(message, id_=id_, skip_db_update=False)

                logger.debug(f"[CUGA] Message processed with ID: {result.id}")
                return result

            result = await process_agent_events(
                event_iterator, agent_message, cast("SendMessageFunctionType", force_db_update_send_message)
            )

            logger.debug("[CUGA] Agent run finished successfully.")
            logger.debug(f"[CUGA] Agent output: {result}")

        except Exception as e:
            logger.error(f"[CUGA] Error in message_response: {e}")
            logger.error(f"[CUGA] An error occurred: {e!s}")
            logger.error(f"[CUGA] Traceback: {traceback.format_exc()}")

            # Check if error is related to Playwright installation
            error_str = str(e).lower()
            if "playwright install" in error_str:
                msg = (
                    "Playwright is not installed. Please install Playwright Chromium using: "
                    "uv run -m playwright install chromium"
                )
                raise ValueError(msg) from e

            raise
        else:
            return result