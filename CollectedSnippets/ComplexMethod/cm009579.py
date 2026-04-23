def _backwards_compat_tool_calls(cls, values: dict) -> Any:
        check_additional_kwargs = not any(
            values.get(k)
            for k in ("tool_calls", "invalid_tool_calls", "tool_call_chunks")
        )
        if check_additional_kwargs and (
            raw_tool_calls := values.get("additional_kwargs", {}).get("tool_calls")
        ):
            try:
                if issubclass(cls, AIMessageChunk):
                    values["tool_call_chunks"] = default_tool_chunk_parser(
                        raw_tool_calls
                    )
                else:
                    parsed_tool_calls, parsed_invalid_tool_calls = default_tool_parser(
                        raw_tool_calls
                    )
                    values["tool_calls"] = parsed_tool_calls
                    values["invalid_tool_calls"] = parsed_invalid_tool_calls
            except Exception:
                logger.debug("Failed to parse tool calls", exc_info=True)

        # Ensure "type" is properly set on all tool call-like dicts.
        if tool_calls := values.get("tool_calls"):
            values["tool_calls"] = [
                create_tool_call(
                    **{k: v for k, v in tc.items() if k not in {"type", "extras"}}
                )
                for tc in tool_calls
            ]
        if invalid_tool_calls := values.get("invalid_tool_calls"):
            values["invalid_tool_calls"] = [
                create_invalid_tool_call(**{k: v for k, v in tc.items() if k != "type"})
                for tc in invalid_tool_calls
            ]

        if tool_call_chunks := values.get("tool_call_chunks"):
            values["tool_call_chunks"] = [
                create_tool_call_chunk(**{k: v for k, v in tc.items() if k != "type"})
                for tc in tool_call_chunks
            ]

        return values