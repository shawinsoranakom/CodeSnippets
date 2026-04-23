def content_blocks(self) -> list[types.ContentBlock]:
        """Return standard, typed `ContentBlock` dicts from the message."""
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
                    return translator["translate_content_chunk"](self)
                except NotImplementedError:
                    pass

        # Otherwise, use best-effort parsing
        blocks = super().content_blocks

        if (
            self.tool_call_chunks
            and not self.content
            and self.chunk_position != "last"  # keep tool_calls if aggregated
        ):
            blocks = [
                block
                for block in blocks
                if block["type"] not in {"tool_call", "invalid_tool_call"}
            ]
            for tool_call_chunk in self.tool_call_chunks:
                tc: types.ToolCallChunk = {
                    "type": "tool_call_chunk",
                    "id": tool_call_chunk.get("id"),
                    "name": tool_call_chunk.get("name"),
                    "args": tool_call_chunk.get("args"),
                }
                if (idx := tool_call_chunk.get("index")) is not None:
                    tc["index"] = idx
                blocks.append(tc)

        # Best-effort reasoning extraction from additional_kwargs
        # Only add reasoning if not already present
        # Insert before all other blocks to keep reasoning at the start
        has_reasoning = any(block.get("type") == "reasoning" for block in blocks)
        if not has_reasoning and (
            reasoning_block := _extract_reasoning_from_additional_kwargs(self)
        ):
            blocks.insert(0, reasoning_block)

        return blocks