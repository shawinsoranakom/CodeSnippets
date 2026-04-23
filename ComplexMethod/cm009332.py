def _get_request_payload(
        self,
        input_: LanguageModelInput,
        *,
        stop: list[str] | None = None,
        **kwargs: Any,
    ) -> dict:
        payload = super()._get_request_payload(input_, stop=stop, **kwargs)
        for message in payload["messages"]:
            if message["role"] == "tool" and isinstance(message["content"], list):
                message["content"] = json.dumps(message["content"])
            elif message["role"] == "assistant" and isinstance(
                message["content"], list
            ):
                # DeepSeek API expects assistant content to be a string, not a list.
                # Extract text blocks and join them, or use empty string if none exist.
                text_parts = [
                    block.get("text", "")
                    for block in message["content"]
                    if isinstance(block, dict) and block.get("type") == "text"
                ]
                message["content"] = "".join(text_parts) if text_parts else ""

        # Azure-hosted DeepSeek does not support the dict/object form of
        # tool_choice (e.g. {"type": "function", "function": {"name": "..."}}).
        # It only accepts string values: "none", "auto", or "required".
        # Convert the unsupported dict form to "required", which is the closest
        # string equivalent — it forces the model to call a tool without
        # constraining which one. In the common with_structured_output() case
        # only a single tool is bound, so the behavior is effectively identical.
        if self._is_azure_endpoint and isinstance(payload.get("tool_choice"), dict):
            payload["tool_choice"] = "required"

        return payload