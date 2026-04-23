def content_blocks(self) -> list[types.ContentBlock]:
        r"""Load content blocks from the message content.

        !!! version-added "Added in `langchain-core` 1.0.0"

        """
        # Needed here to avoid circular import, as these classes import BaseMessages
        from langchain_core.messages.block_translators.anthropic import (  # noqa: PLC0415
            _convert_to_v1_from_anthropic_input,
        )
        from langchain_core.messages.block_translators.bedrock_converse import (  # noqa: PLC0415
            _convert_to_v1_from_converse_input,
        )
        from langchain_core.messages.block_translators.google_genai import (  # noqa: PLC0415
            _convert_to_v1_from_genai_input,
        )
        from langchain_core.messages.block_translators.langchain_v0 import (  # noqa: PLC0415
            _convert_v0_multimodal_input_to_v1,
        )
        from langchain_core.messages.block_translators.openai import (  # noqa: PLC0415
            _convert_to_v1_from_chat_completions_input,
        )

        blocks: list[types.ContentBlock] = []
        content = (
            # Transpose string content to list, otherwise assumed to be list
            [self.content]
            if isinstance(self.content, str) and self.content
            else self.content
        )
        for item in content:
            if isinstance(item, str):
                # Plain string content is treated as a text block
                blocks.append({"type": "text", "text": item})
            elif isinstance(item, dict):
                item_type = item.get("type")
                if item_type not in types.KNOWN_BLOCK_TYPES:
                    # Handle all provider-specific or None type blocks as non-standard -
                    # we'll come back to these later
                    blocks.append({"type": "non_standard", "value": item})
                else:
                    # Guard against v0 blocks that share the same `type` keys
                    if "source_type" in item:
                        blocks.append({"type": "non_standard", "value": item})
                        continue

                    # This can't be a v0 block (since they require `source_type`),
                    # so it's a known v1 block type
                    blocks.append(cast("types.ContentBlock", item))

        # Subsequent passes: attempt to unpack non-standard blocks.
        # This is the last stop - if we can't parse it here, it is left as non-standard
        for parsing_step in [
            _convert_v0_multimodal_input_to_v1,
            _convert_to_v1_from_chat_completions_input,
            _convert_to_v1_from_anthropic_input,
            _convert_to_v1_from_genai_input,
            _convert_to_v1_from_converse_input,
        ]:
            blocks = parsing_step(blocks)
        return blocks