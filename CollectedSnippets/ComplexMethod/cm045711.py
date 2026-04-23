def _extract_system_prompt(messages: list[dict]) -> list[dict] | None:
        """Extract system prompts from messages for Bedrock's system parameter."""
        system_prompts = []
        for msg in messages:
            if msg.get("role") == BedrockChat.ROLE_SYSTEM:
                content = msg.get("content", "")
                if isinstance(content, str):
                    system_prompts.append({"text": content})
                elif isinstance(content, list):
                    for item in content:
                        if isinstance(item, str):
                            system_prompts.append({"text": item})
                        elif isinstance(item, dict) and item.get("type") == "text":
                            system_prompts.append({"text": item.get("text", "")})

        return system_prompts if system_prompts else None