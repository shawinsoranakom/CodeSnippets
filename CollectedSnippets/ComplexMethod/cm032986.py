def message_to_section(message: dict[str, Any]) -> tuple[TextSection, dict[str, str]]:
    """Convert Gmail message to text section and metadata."""
    link = f"https://mail.google.com/mail/u/0/#inbox/{message['id']}"

    payload = message.get("payload", {})
    headers = payload.get("headers", [])
    metadata: dict[str, Any] = {}

    for header in headers:
        name = header.get("name", "").lower()
        value = header.get("value", "")
        if name in EMAIL_FIELDS:
            metadata[name] = value
        if name == "subject":
            metadata["subject"] = value
        if name == "date":
            metadata["updated_at"] = value

    if labels := message.get("labelIds"):
        metadata["labels"] = labels

    message_data = ""
    for name, value in metadata.items():
        if name != "updated_at":
            message_data += f"{name}: {value}\n"

    message_body_text: str = get_message_body(payload)
    return TextSection(link=link, text=message_body_text + message_data), metadata