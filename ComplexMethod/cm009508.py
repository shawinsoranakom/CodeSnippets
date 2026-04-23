def _get_output_messages(
        self, output_val: str | BaseMessage | Sequence[BaseMessage] | dict
    ) -> list[BaseMessage]:
        # If dictionary, try to pluck the single key representing messages
        if isinstance(output_val, dict):
            if self.output_messages_key:
                key = self.output_messages_key
            elif len(output_val) == 1:
                key = next(iter(output_val.keys()))
            else:
                key = "output"
            # If you are wrapping a chat model directly
            # The output is actually this weird generations object
            if key not in output_val and "generations" in output_val:
                output_val = output_val["generations"][0][0]["message"]
            else:
                output_val = output_val[key]

        if isinstance(output_val, str):
            return [AIMessage(content=output_val)]
        # If value is a single message, convert to a list
        if isinstance(output_val, BaseMessage):
            return [output_val]
        if isinstance(output_val, (list, tuple)):
            return list(output_val)
        msg = (
            f"Expected str, BaseMessage, list[BaseMessage], or tuple[BaseMessage]. "
            f"Got {output_val}."
        )
        raise ValueError(msg)