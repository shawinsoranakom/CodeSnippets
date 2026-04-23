async def retrieve_messages(self) -> Data:
        sender_type = self.sender_type
        sender_name = self.sender_name
        session_id = self.session_id
        context_id = self.context_id
        n_messages = self.n_messages
        order = "DESC" if self.order == "Descending" else "ASC"

        if sender_type == "Machine and User":
            sender_type = None

        if self.memory and not hasattr(self.memory, "aget_messages"):
            memory_name = type(self.memory).__name__
            err_msg = f"External Memory object ({memory_name}) must have 'aget_messages' method."
            raise AttributeError(err_msg)
        # Check if n_messages is None or 0
        if n_messages == 0:
            stored = []
        elif self.memory:
            # override session_id
            self.memory.session_id = session_id
            self.memory.context_id = context_id

            stored = await self.memory.aget_messages()
            # langchain memories are supposed to return messages in ascending order

            if n_messages:
                stored = stored[-n_messages:]  # Get last N messages first

            if order == "DESC":
                stored = stored[::-1]  # Then reverse if needed

            stored = [Message.from_lc_message(m) for m in stored]
            if sender_type:
                expected_type = MESSAGE_SENDER_AI if sender_type == MESSAGE_SENDER_AI else MESSAGE_SENDER_USER
                stored = [m for m in stored if m.type == expected_type]
        else:
            # For internal memory, we always fetch the last N messages by ordering by DESC
            stored = await aget_messages(
                sender=sender_type,
                sender_name=sender_name,
                session_id=session_id,
                context_id=context_id,
                limit=10000,
                order=order,
            )
            if n_messages:
                stored = stored[-n_messages:]  # Get last N messages

        # self.status = stored
        return cast("Data", stored)