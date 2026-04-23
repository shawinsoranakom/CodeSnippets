def format_msg(self, messages: Union[str, "Message", list[dict], list["Message"], list[str]]) -> list[dict]:
        """convert messages to list[dict]."""
        from metagpt.schema import Message

        if not isinstance(messages, list):
            messages = [messages]

        processed_messages = []
        for msg in messages:
            if isinstance(msg, str):
                processed_messages.append({"role": "user", "content": msg})
            elif isinstance(msg, dict):
                assert set(msg.keys()) == set(["role", "content"])
                processed_messages.append(msg)
            elif isinstance(msg, Message):
                images = msg.metadata.get(IMAGES)
                processed_msg = self._user_msg(msg=msg.content, images=images) if images else msg.to_dict()
                processed_messages.append(processed_msg)
            else:
                raise ValueError(
                    f"Only support message type are: str, Message, dict, but got {type(messages).__name__}!"
                )
        return processed_messages