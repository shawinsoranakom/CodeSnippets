def format_msg(self, messages: Union[str, "Message", list[dict], list["Message"], list[str]]) -> list[dict]:
        """convert messages to list[dict]."""
        from metagpt.schema import Message

        if not isinstance(messages, list):
            messages = [messages]

        # REF: https://ai.google.dev/tutorials/python_quickstart
        # As a dictionary, the message requires `role` and `parts` keys.
        # The role in a conversation can either be the `user`, which provides the prompts,
        # or `model`, which provides the responses.
        processed_messages = []
        for msg in messages:
            if isinstance(msg, str):
                processed_messages.append({"role": "user", "parts": [msg]})
            elif isinstance(msg, dict):
                assert set(msg.keys()) == set(["role", "parts"])
                processed_messages.append(msg)
            elif isinstance(msg, Message):
                processed_messages.append({"role": "user" if msg.role == "user" else "model", "parts": [msg.content]})
            else:
                raise ValueError(
                    f"Only support message type are: str, Message, dict, but got {type(messages).__name__}!"
                )
        return processed_messages