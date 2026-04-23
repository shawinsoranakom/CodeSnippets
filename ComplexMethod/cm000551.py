def _update_conversation(
        self,
        prompt: list[dict[str, Any]],
        response: Any,
        tool_outputs: list[dict[str, Any]] | None = None,
    ):
        """Update conversation history with response and tool outputs.

        ``response`` must be an ``LLMResponse`` (from ``backend.blocks.llm``),
        **not** an ``LLMLoopResponse``. The method accesses ``.raw_response``
        and ``.reasoning`` attributes on the passed object.
        """
        converted = _convert_raw_response_to_dict(response.raw_response)

        if isinstance(converted, list):
            # Responses API: output items are already individual dicts
            has_tool_calls = any(
                item.get("type") == "function_call" for item in converted
            )
            if response.reasoning and not has_tool_calls:
                prompt.append(
                    {
                        "role": "assistant",
                        "content": f"[Reasoning]: {response.reasoning}",
                    }
                )
            prompt.extend(converted)
        else:
            # Chat Completions / Anthropic: single assistant message dict
            has_tool_calls = isinstance(converted.get("content"), list) and any(
                item.get("type") == "tool_use" for item in converted.get("content", [])
            )
            if response.reasoning and not has_tool_calls:
                prompt.append(
                    {
                        "role": "assistant",
                        "content": f"[Reasoning]: {response.reasoning}",
                    }
                )
            prompt.append(converted)

        if tool_outputs:
            prompt.extend(tool_outputs)