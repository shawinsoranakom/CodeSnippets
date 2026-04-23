def get_last_user_message(messages: Messages, include_buckets: bool = True) -> str:
    user_messages = []
    for message in messages[::-1]:
        if message.get("role") == "user" or not user_messages:
            if message.get("role") != "user":
                continue
            content = message.get("content")
            if include_buckets:
                content = to_string(content).strip()
            if isinstance(content, str):
                user_messages.append(content)
            else:
                for content_item in content:
                    if content_item.get("type") == "text":
                        content = content_item.get("text").strip()
                        if content:
                            user_messages.append(content)
        else:
            return "\n".join(user_messages[::-1])
    return "\n".join(user_messages[::-1])