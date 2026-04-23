def _get_last_query_index(messages: list[Message]) -> int:
    """Find the last user query index, excluding wrapped tool responses."""
    last_query_index = len(messages) - 1
    for idx in range(len(messages) - 1, -1, -1):
        message = messages[idx]
        if message["role"] != "user":
            continue

        user_text = ""
        is_plain_text = True
        for content in message["content"]:
            if content["type"] != "text":
                is_plain_text = False
                break
            user_text += content["value"]

        if not is_plain_text:
            continue

        if not (user_text.startswith("<tool_response>") and user_text.endswith("</tool_response>")):
            last_query_index = idx
            break

    return last_query_index