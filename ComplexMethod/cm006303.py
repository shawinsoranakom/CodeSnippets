def _convert_to_langwatch_type(self, value):
        from langchain_core.messages import BaseMessage
        from langwatch.langchain import langchain_message_to_chat_message, langchain_messages_to_chat_messages
        from lfx.schema.message import Message

        if isinstance(value, dict):
            value = {key: self._convert_to_langwatch_type(val) for key, val in value.items()}
        elif isinstance(value, list):
            value = [self._convert_to_langwatch_type(v) for v in value]
        elif isinstance(value, Message):
            if "prompt" in value:
                prompt = value.load_lc_prompt()
                if len(prompt.input_variables) == 0 and all(isinstance(m, BaseMessage) for m in prompt.messages):
                    value = langchain_messages_to_chat_messages([cast("list[BaseMessage]", prompt.messages)])
                else:
                    value = cast("dict", value.load_lc_prompt())
            elif value.sender:
                value = langchain_message_to_chat_message(value.to_lc_message())
            else:
                value = cast("dict", value.to_lc_document())
        elif isinstance(value, Data):
            value = cast("dict", value.to_lc_document())
        return value