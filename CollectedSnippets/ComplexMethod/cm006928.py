def _ensure_message_required_fields(self, message: Message) -> None:
        """Ensure message has required fields for storage (session_id, sender, sender_name).

        Only sets default values if the fields are not already provided.
        """
        from lfx.utils.constants import MESSAGE_SENDER_AI, MESSAGE_SENDER_NAME_AI

        # Set default session_id from graph if not already set
        if (
            not message.session_id
            and hasattr(self, "graph")
            and hasattr(self.graph, "session_id")
            and self.graph.session_id
        ):
            session_id = (
                UUID(self.graph.session_id) if isinstance(self.graph.session_id, str) else self.graph.session_id
            )
            message.session_id = session_id

        # Set default sender if not set (preserves existing values)
        if not message.sender:
            message.sender = MESSAGE_SENDER_AI

        # Set default sender_name if not set (preserves existing values)
        if not message.sender_name:
            message.sender_name = MESSAGE_SENDER_NAME_AI