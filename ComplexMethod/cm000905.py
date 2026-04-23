def _format_sdk_content_blocks(blocks: list) -> list[dict[str, Any]]:
    """Convert SDK content blocks to transcript format.

    Handles TextBlock, ToolUseBlock, ToolResultBlock, and ThinkingBlock.
    Raw dicts (e.g. ``redacted_thinking`` blocks that the SDK may not have
    a typed class for) are passed through verbatim to preserve them in the
    transcript.  Unknown typed block objects are logged and skipped.
    """
    result: list[dict[str, Any]] = []
    for block in blocks or []:
        if isinstance(block, TextBlock):
            result.append({"type": "text", "text": block.text})
        elif isinstance(block, ToolUseBlock):
            result.append(
                {
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                }
            )
        elif isinstance(block, ToolResultBlock):
            tool_result_entry: dict[str, Any] = {
                "type": "tool_result",
                "tool_use_id": block.tool_use_id,
                "content": block.content,
            }
            if block.is_error:
                tool_result_entry["is_error"] = True
            result.append(tool_result_entry)
        elif isinstance(block, ThinkingBlock):
            result.append(
                {
                    "type": "thinking",
                    "thinking": block.thinking,
                    "signature": block.signature,
                }
            )
        elif isinstance(block, dict) and "type" in block:
            # Preserve raw dict blocks (e.g. redacted_thinking) verbatim.
            result.append(block)
        else:
            logger.warning(
                "[SDK] Unknown content block type: %s."
                " This may indicate a new SDK version with additional block types.",
                type(block).__name__,
            )
    return result