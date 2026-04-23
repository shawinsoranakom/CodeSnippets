def init_tool_calls(self) -> Self:
        """Initialize tool calls from tool call chunks.

        Returns:
            The values with tool calls initialized.

        Raises:
            ValueError: If the tool call chunks are malformed.
        """
        if not self.tool_call_chunks:
            if self.tool_calls:
                self.tool_call_chunks = [
                    create_tool_call_chunk(
                        name=tc["name"],
                        args=json.dumps(tc["args"]),
                        id=tc["id"],
                        index=None,
                    )
                    for tc in self.tool_calls
                ]
            if self.invalid_tool_calls:
                tool_call_chunks = self.tool_call_chunks
                tool_call_chunks.extend(
                    [
                        create_tool_call_chunk(
                            name=tc["name"], args=tc["args"], id=tc["id"], index=None
                        )
                        for tc in self.invalid_tool_calls
                    ]
                )
                self.tool_call_chunks = tool_call_chunks

            return self
        tool_calls = []
        invalid_tool_calls = []

        def add_chunk_to_invalid_tool_calls(chunk: ToolCallChunk) -> None:
            invalid_tool_calls.append(
                create_invalid_tool_call(
                    name=chunk["name"],
                    args=chunk["args"],
                    id=chunk["id"],
                    error=None,
                )
            )

        for chunk in self.tool_call_chunks:
            try:
                args_ = parse_partial_json(chunk["args"]) if chunk["args"] else {}
                if isinstance(args_, dict):
                    tool_calls.append(
                        create_tool_call(
                            name=chunk["name"] or "",
                            args=args_,
                            id=chunk["id"],
                        )
                    )
                else:
                    add_chunk_to_invalid_tool_calls(chunk)
            except Exception:
                add_chunk_to_invalid_tool_calls(chunk)
        self.tool_calls = tool_calls
        self.invalid_tool_calls = invalid_tool_calls

        if (
            self.chunk_position == "last"
            and self.tool_call_chunks
            and self.response_metadata.get("output_version") == "v1"
            and isinstance(self.content, list)
        ):
            id_to_tc: dict[str, types.ToolCall] = {
                cast("str", tc.get("id")): {
                    "type": "tool_call",
                    "name": tc["name"],
                    "args": tc["args"],
                    "id": tc.get("id"),
                }
                for tc in self.tool_calls
                if "id" in tc
            }
            for idx, block in enumerate(self.content):
                if (
                    isinstance(block, dict)
                    and block.get("type") == "tool_call_chunk"
                    and (call_id := block.get("id"))
                    and call_id in id_to_tc
                ):
                    self.content[idx] = cast("dict[str, Any]", id_to_tc[call_id])
                    if "extras" in block:
                        # mypy does not account for instance check for dict above
                        self.content[idx]["extras"] = block["extras"]  # type: ignore[index]

        return self