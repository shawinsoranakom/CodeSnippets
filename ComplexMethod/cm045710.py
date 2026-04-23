def _convert_messages_to_bedrock_format(messages: list[dict]) -> list[dict]:
        """Convert OpenAI-style messages to AWS Bedrock Converse API format."""
        bedrock_messages = []
        for msg in messages:
            role = msg.get("role", BedrockChat.ROLE_USER)
            content = msg.get("content", "")

            # Validate role
            if role not in BedrockChat._SUPPORTED_ROLES:
                raise ValueError(
                    f"Unsupported message role: '{role}'. "
                    f"Expected one of: {BedrockChat._SUPPORTED_ROLES}"
                )

            # System messages are handled separately in Bedrock
            if role == BedrockChat.ROLE_SYSTEM:
                continue

            # Bedrock uses "user" and "assistant" roles directly
            # No transformation needed for these roles

            # Handle content - can be string or list of content blocks
            if isinstance(content, str):
                bedrock_content = [{"text": content}]
            elif isinstance(content, list):
                bedrock_content = []
                for item in content:
                    if isinstance(item, str):
                        bedrock_content.append({"text": item})
                    elif isinstance(item, dict):
                        if item.get("type") == "text":
                            bedrock_content.append({"text": item.get("text", "")})
                        elif item.get("type") == "image_url":
                            # Handle image content if needed
                            bedrock_content.append({"text": "[Image content]"})
            else:
                bedrock_content = [{"text": str(content)}]

            bedrock_messages.append({"role": role, "content": bedrock_content})

        return bedrock_messages