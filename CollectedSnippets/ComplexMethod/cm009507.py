def _get_input_messages(
        self, input_val: str | BaseMessage | Sequence[BaseMessage] | dict
    ) -> list[BaseMessage]:
        # If dictionary, try to pluck the single key representing messages
        if isinstance(input_val, dict):
            if self.input_messages_key:
                key = self.input_messages_key
            elif len(input_val) == 1:
                key = next(iter(input_val.keys()))
            else:
                key = "input"
            input_val = input_val[key]

        # If value is a string, convert to a human message
        if isinstance(input_val, str):
            return [HumanMessage(content=input_val)]
        # If value is a single message, convert to a list
        if isinstance(input_val, BaseMessage):
            return [input_val]
        # If value is a list or tuple...
        if isinstance(input_val, (list, tuple)):
            # Handle empty case
            if len(input_val) == 0:
                return list(input_val)
            # If is a list of list, then return the first value
            # This occurs for chat models - since we batch inputs
            if isinstance(input_val[0], list):
                if len(input_val) != 1:
                    msg = f"Expected a single list of messages. Got {input_val}."
                    raise ValueError(msg)
                return input_val[0]
            return list(input_val)
        msg = (
            f"Expected str, BaseMessage, list[BaseMessage], or tuple[BaseMessage]. "
            f"Got {input_val}."
        )
        raise ValueError(msg)