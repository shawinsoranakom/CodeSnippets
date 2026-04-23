def caculate_prompt_tokens(messages: Messages) -> int:
    """Calculate the total number of tokens in messages"""
    token_count = 1  # Bos Token
    for message in messages:
        if isinstance(message.get("content"), str):
            token_count += math.floor(len(message["content"].encode("utf-8")) / 4)
            token_count += 4  # Role and start/end message token
        elif isinstance(message.get("content"), list):
            for item in message["content"]:
                if isinstance(item, str):
                    token_count += math.floor(len(item.encode("utf-8")) / 4)
                elif (
                    isinstance(item, dict)
                    and "text" in item
                    and isinstance(item["text"], str)
                ):
                    token_count += math.floor(len(item["text"].encode("utf-8")) / 4)
                token_count += 4  # Role and start/end message token
    return token_count