def format_messages_for_yupp(messages: Messages) -> str:
    if not messages:
        return ""

    if len(messages) == 1 and isinstance(messages[0].get("content"), str):
        return messages[0].get("content", "").strip()

    formatted = []

    system_messages = [
        msg for msg in messages if msg.get("role") in ["developer", "system"]
    ]
    if system_messages:
        for sys_msg in system_messages:
            content = sys_msg.get("content", "")
            formatted.append(content)

    user_assistant_msgs = [
        msg for msg in messages if msg.get("role") in ["user", "assistant"]
    ]
    for msg in user_assistant_msgs:
        role = "Human" if msg.get("role") == "user" else "Assistant"
        content = msg.get("content", "")
        for part in content if isinstance(content, list) else [{"text": content}]:
            if part.get("text", "").strip():
                formatted.append(f"\n\n{role}: {part.get('text', '')}")

    if not formatted or not formatted[-1].strip().startswith("Assistant:"):
        formatted.append("\n\nAssistant:")

    result = "".join(formatted)
    if result.startswith("\n\n"):
        result = result[2:]

    return result