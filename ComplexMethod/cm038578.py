def _postprocess_messages(messages: list[ConversationMessage]) -> None:
    # per the Transformers docs & maintainers, tool call arguments in
    # assistant-role messages with tool_calls need to be dicts not JSON str -
    # this is how tool-use chat templates will expect them moving forwards
    # so, for messages that have tool_calls, parse the string (which we get
    # from openAI format) to dict
    for message in messages:
        if message["role"] == "assistant" and "tool_calls" in message:
            tool_calls = message.get("tool_calls")
            if not isinstance(tool_calls, list):
                continue

            if len(tool_calls) == 0:
                # Drop empty tool_calls to keep templates on the normal assistant path.
                message.pop("tool_calls", None)
                continue

            for item in tool_calls:
                # if arguments is None or empty string, set to {}
                if content := item["function"].get("arguments"):
                    if not isinstance(content, (dict, list)):
                        item["function"]["arguments"] = json.loads(content)
                else:
                    item["function"]["arguments"] = {}