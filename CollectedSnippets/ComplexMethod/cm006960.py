async def message_response(self) -> Message:
        # First convert the input to string if needed
        text = self.convert_to_string()

        # Get source properties
        source, _, display_name, source_id = self.get_properties_from_source_component()

        # Create or use existing Message object
        if isinstance(self.input_value, Message) and not self.is_connected_to_chat_input():
            message = self.input_value
            # Update message properties
            message.text = text
            # Preserve existing session_id from the incoming message if it exists
            existing_session_id = message.session_id
        else:
            message = Message(text=text)
            existing_session_id = None

        # Set message properties
        message.sender = self.sender
        message.sender_name = self.sender_name
        # Preserve session_id from incoming message, or use component/graph session_id
        message.session_id = (
            self.session_id or existing_session_id or (self.graph.session_id if hasattr(self, "graph") else None) or ""
        )
        message.context_id = self.context_id
        message.flow_id = self.graph.flow_id if hasattr(self, "graph") else None
        message.properties.source = self._build_source(source_id, display_name, source)

        # Store message if needed
        if message.session_id and self.should_store_message:
            stored_message = await self.send_message(message)
            self.message.value = stored_message
            message = stored_message

        # Set accumulated token usage from all upstream LLM vertices.
        # This must happen AFTER send_message() because streaming captures
        # usage from chunks and would overwrite accumulated totals.
        if hasattr(self, "_vertex") and self._vertex is not None:
            accumulated_usage = self._vertex._accumulate_upstream_token_usage()  # noqa: SLF001
            if accumulated_usage:
                message.properties.usage = accumulated_usage
                if self.should_store_message and message.get_id():
                    message = await self._update_stored_message(message)
                    await self._send_message_event(message, id_=message.get_id())

        self.status = message
        return message