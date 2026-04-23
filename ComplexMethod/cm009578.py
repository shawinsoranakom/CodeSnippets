def content_blocks(self) -> list[types.ContentBlock]:
        """Return standard, typed `ContentBlock` dicts from the message.

        If the message has a known model provider, use the provider-specific translator
        first before falling back to best-effort parsing. For details, see the property
        on `BaseMessage`.
        """
        if self.response_metadata.get("output_version") == "v1":
            return cast("list[types.ContentBlock]", self.content)

        model_provider = self.response_metadata.get("model_provider")
        if model_provider:
            from langchain_core.messages.block_translators import (  # noqa: PLC0415
                get_translator,
            )

            translator = get_translator(model_provider)
            if translator:
                try:
                    return translator["translate_content"](self)
                except NotImplementedError:
                    pass

        # Otherwise, use best-effort parsing
        blocks = super().content_blocks

        if self.tool_calls:
            # Add from tool_calls if missing from content
            content_tool_call_ids = {
                block.get("id")
                for block in self.content
                if isinstance(block, dict) and block.get("type") == "tool_call"
            }
            for tool_call in self.tool_calls:
                if (id_ := tool_call.get("id")) and id_ not in content_tool_call_ids:
                    tool_call_block: types.ToolCall = {
                        "type": "tool_call",
                        "id": id_,
                        "name": tool_call["name"],
                        "args": tool_call["args"],
                    }
                    if "index" in tool_call:
                        tool_call_block["index"] = tool_call["index"]  # type: ignore[typeddict-item]
                    if "extras" in tool_call:
                        tool_call_block["extras"] = tool_call["extras"]  # type: ignore[typeddict-item]
                    blocks.append(tool_call_block)

        # Best-effort reasoning extraction from additional_kwargs
        # Only add reasoning if not already present
        # Insert before all other blocks to keep reasoning at the start
        has_reasoning = any(block.get("type") == "reasoning" for block in blocks)
        if not has_reasoning and (
            reasoning_block := _extract_reasoning_from_additional_kwargs(self)
        ):
            blocks.insert(0, reasoning_block)

        return blocks