def init_server_tool_calls(self) -> Self:
        """Initialize server tool calls.

        Parse `server_tool_call_chunks` from
        [`ServerToolCallChunk`][langchain.messages.ServerToolCallChunk] objects.
        """
        if (
            self.chunk_position == "last"
            and self.response_metadata.get("output_version") == "v1"
            and isinstance(self.content, list)
        ):
            for idx, block in enumerate(self.content):
                if (
                    isinstance(block, dict)
                    and block.get("type")
                    in {"server_tool_call", "server_tool_call_chunk"}
                    and (args_str := block.get("args"))
                    and isinstance(args_str, str)
                ):
                    try:
                        args = json.loads(args_str)
                        if isinstance(args, dict):
                            self.content[idx]["type"] = "server_tool_call"  # type: ignore[index]
                            self.content[idx]["args"] = args  # type: ignore[index]
                    except json.JSONDecodeError:
                        pass
        return self