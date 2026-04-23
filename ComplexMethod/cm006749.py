def build_conversation_context(self) -> list[BaseMessage]:
        """Create conversation context from input and chat history."""
        context: list[BaseMessage] = []

        # Add chat history to maintain chronological order
        if hasattr(self, "chat_history") and self.chat_history:
            if isinstance(self.chat_history, Data):
                context.append(self.chat_history.to_lc_message())
            elif isinstance(self.chat_history, list):
                if all(isinstance(m, Message) for m in self.chat_history):
                    context.extend([m.to_lc_message() for m in self.chat_history])
                else:
                    # Assume list of Data objects, let data_to_messages handle validation
                    try:
                        context.extend(data_to_messages(self.chat_history))
                    except (AttributeError, TypeError) as e:
                        error_message = f"Invalid chat_history list contents: {e}"
                        raise ValueError(error_message) from e
            else:
                # Reject all other types (strings, numbers, etc.)
                type_name = type(self.chat_history).__name__
                error_message = (
                    f"chat_history must be a Data object, list of Data/Message objects, or None. Got: {type_name}"
                )
                raise ValueError(error_message)

        # Then add current input to maintain chronological order
        if hasattr(self, "input_value") and self.input_value:
            if isinstance(self.input_value, Message):
                context.append(self.input_value.to_lc_message())
            else:
                context.append(HumanMessage(content=str(self.input_value)))

        return context