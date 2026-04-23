def _convert_messages_to_ollama_messages(
        self, messages: list[BaseMessage]
    ) -> Sequence[Message]:
        """Convert a BaseMessage list to list of messages for Ollama to consume.

        Args:
            messages: List of BaseMessage to convert.

        Returns:
            List of messages in Ollama format.
        """
        messages = list(messages)  # shallow copy to avoid mutating caller's list
        for idx, message in enumerate(messages):
            # Handle message content written in v1 format
            if (
                isinstance(message, AIMessage)
                and message.response_metadata.get("output_version") == "v1"
            ):
                # Unpack known v1 content to Ollama format for the request
                # Most types are passed through unchanged
                messages[idx] = message.model_copy(
                    update={
                        "content": _convert_from_v1_to_ollama(
                            cast("list[types.ContentBlock]", message.content),
                            message.response_metadata.get("model_provider"),
                        )
                    }
                )

        ollama_messages: list = []
        for message in messages:
            role: str
            tool_call_id: str | None = None
            tool_calls: list[dict[str, Any]] | None = None
            if isinstance(message, HumanMessage):
                role = "user"
            elif isinstance(message, AIMessage):
                role = "assistant"
                tool_calls = (
                    [
                        _lc_tool_call_to_openai_tool_call(tool_call)
                        for tool_call in message.tool_calls
                    ]
                    if message.tool_calls
                    else None
                )
            elif isinstance(message, SystemMessage):
                role = "system"
            elif isinstance(message, ChatMessage):
                role = message.role
            elif isinstance(message, ToolMessage):
                role = "tool"
                tool_call_id = message.tool_call_id
            else:
                msg = "Received unsupported message type for Ollama."
                raise TypeError(msg)

            content = ""
            images = []
            if isinstance(message.content, str):
                content = message.content
            else:  # List
                for content_part in message.content:
                    if isinstance(content_part, str):
                        content += f"\n{content_part}"
                    elif content_part.get("type") == "text":
                        content += f"\n{content_part['text']}"
                    elif content_part.get("type") == "tool_use":
                        continue
                    elif content_part.get("type") == "image_url":
                        image_url = None
                        temp_image_url = content_part.get("image_url")
                        if isinstance(temp_image_url, str):
                            image_url = temp_image_url
                        elif (
                            isinstance(temp_image_url, dict)
                            and "url" in temp_image_url
                            and isinstance(temp_image_url["url"], str)
                        ):
                            image_url = temp_image_url["url"]
                        else:
                            msg = (
                                "Only string image_url or dict with string 'url' "
                                "inside content parts are supported."
                            )
                            raise ValueError(msg)

                        image_url_components = image_url.split(",")
                        # Support data:image/jpeg;base64,<image> format
                        # and base64 strings
                        if len(image_url_components) > 1:
                            images.append(image_url_components[1])
                        else:
                            images.append(image_url_components[0])
                    elif is_data_content_block(content_part):
                        # Handles v1 "image" type
                        image = _get_image_from_data_content_block(content_part)
                        images.append(image)
                    else:
                        msg = (
                            "Unsupported message content type. "
                            "Must either have type 'text' or type 'image_url' "
                            "with a string 'image_url' field."
                        )
                        raise ValueError(msg)
            # Should convert to ollama.Message once role includes tool, and tool_call_id
            # is in Message
            msg_: dict = {
                "role": role,
                "content": content,
                "images": images,
            }
            if tool_calls:
                msg_["tool_calls"] = tool_calls
            if tool_call_id:
                msg_["tool_call_id"] = tool_call_id
            if isinstance(message, AIMessage):
                thinking = message.additional_kwargs.get("reasoning_content")
                if thinking is not None:
                    msg_["thinking"] = thinking
            ollama_messages.append(msg_)

        return ollama_messages