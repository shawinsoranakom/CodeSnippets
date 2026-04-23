def _adapt_chat_messages_for_mistral_instruct(
        self, messages: list[ChatCompletionMessageParam]
    ) -> list[ChatCompletionMessageParam]:
        """
        Munge the messages to be compatible with the mistral-7b-instruct chat
        template, which:
        - only supports 'user' and 'assistant' roles.
        - expects messages to alternate between user/assistant roles.

        See details here:
        https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2#instruction-format
        """
        # Use Any for working list since we do runtime type transformations
        adapted_messages: list[Any] = []
        for message in messages:
            # convert 'system' role to 'user' role as mistral-7b-instruct does
            # not support 'system'
            if message["role"] == ChatMessage.Role.SYSTEM:
                message["role"] = ChatMessage.Role.USER

            if (
                len(adapted_messages) == 0
                or message["role"] != (last_message := adapted_messages[-1])["role"]
            ):
                adapted_messages.append(message)
            else:
                if not message.get("content"):
                    continue

                # if the curr message has the same role as the previous one,
                # concat the current message content to the prev message
                if message["role"] == "user" and last_message["role"] == "user":
                    # user messages can contain other types of content blocks
                    if not isinstance(last_message["content"], list):
                        last_message["content"] = [
                            {"type": "text", "text": last_message["content"]}
                        ]

                    last_message["content"].extend(
                        message["content"]
                        if isinstance(message["content"], list)
                        else [{"type": "text", "text": message["content"]}]
                    )
                elif message["role"] != "user" and last_message["role"] != "user":
                    # Non-user messages have string content
                    prev_content = str(last_message.get("content") or "")
                    curr_content = str(message.get("content") or "")
                    last_message["content"] = (
                        prev_content + "\n\n" + curr_content
                    ).strip()

        return cast(list[ChatCompletionMessageParam], adapted_messages)