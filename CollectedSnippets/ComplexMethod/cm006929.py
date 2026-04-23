async def send_message(self, message: Message, id_: str | None = None, *, skip_db_update: bool = False):
        """Send a message with optional database update control.

        This is the central method for sending messages in Langflow. It handles:
        - Message storage in the database (unless skipped)
        - Event emission to the frontend
        - Streaming support
        - Error handling and cleanup

        Message ID Rules:
        - Messages only have an ID after being stored in the database
        - If _should_skip_message() returns True, the message is not stored and will not have an ID
        - Always use message.get_id() or message.has_id() to safely check for ID existence
        - Never access message.id directly without checking if it exists first

        Args:
            message: The message to send
            id_: Optional message ID (used for event emission, not database storage)
            skip_db_update: If True, only update in-memory and send event, skip DB write.
                           Useful during streaming to avoid excessive DB round-trips.
                           Note: When skip_db_update=True, the message must already have an ID
                           (i.e., it must have been stored previously).

        Returns:
            Message: The stored message (with ID if stored in database, without ID if skipped)

        Raises:
            ValueError: If skip_db_update=True but message doesn't have an ID
        """
        if self._should_skip_message(message):
            return message

        if hasattr(message, "flow_id") and isinstance(message.flow_id, str):
            message.flow_id = UUID(message.flow_id)

        # Ensure required fields for message storage are set
        self._ensure_message_required_fields(message)

        # If skip_db_update is True and message already has an ID, skip the DB write
        # This path is used during agent streaming to avoid excessive DB round-trips
        # When skip_db_update=True, we require the message to already have an ID
        # because we're updating an existing message, not creating a new one
        if skip_db_update:
            if not message.has_id():
                msg = (
                    "skip_db_update=True requires the message to already have an ID. "
                    "The message must have been stored in the database previously."
                )
                raise ValueError(msg)

            # Create a fresh Message instance for consistency with normal flow
            stored_message = await Message.create(**message.model_dump())
            self._stored_message_id = stored_message.get_id()
            # Still send the event to update the client in real-time
            # Note: If this fails, we don't need DB cleanup since we didn't write to DB
            await self._send_message_event(stored_message, id_=id_)
        else:
            # Normal flow: store/update in database
            stored_message = await self._store_message(message)

            # After _store_message, the message should always have an ID
            # but we use get_id() for safety
            self._stored_message_id = stored_message.get_id()
            try:
                complete_message = ""
                if (
                    self._should_stream_message(stored_message, message)
                    and message is not None
                    and isinstance(message.text, AsyncIterator | Iterator)
                ):
                    complete_message, usage_data = await self._stream_message(message.text, stored_message)
                    stored_message.text = complete_message
                    if complete_message:
                        stored_message.properties.state = "complete"
                    # Set usage data if captured from streaming
                    if usage_data:
                        stored_message.properties.usage = usage_data
                    stored_message = await self._update_stored_message(stored_message)
                    # Send a final add_message event with state="complete" and usage data
                    # This is needed for OpenAI Responses API to capture usage in streaming mode
                    await self._send_message_event(stored_message, id_=self._stored_message_id)
                else:
                    # Only send message event for non-streaming messages
                    await self._send_message_event(stored_message, id_=id_)
            except Exception:
                # remove the message from the database
                # Only delete if the message has an ID
                message_id = stored_message.get_id()
                if message_id:
                    await delete_message(id_=message_id)
                raise
        self.status = stored_message
        return stored_message