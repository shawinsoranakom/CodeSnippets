async def _handle_streamed_tool_delta(
        self,
        event: StreamEvent,
        started_tool_ids: set[str],
        streamed_lengths: Dict[str, int],
    ) -> None:
        if event.type != "tool_call_delta":
            return
        if event.tool_name != "create_file":
            return
        if not event.tool_call_id:
            return

        content = extract_content_from_args(event.tool_arguments)
        if content is None:
            return

        tool_event_id = event.tool_call_id
        if tool_event_id not in started_tool_ids:
            path = (
                extract_path_from_args(event.tool_arguments)
                or self.file_state.path
                or "index.html"
            )
            await self._send(
                "toolStart",
                data={
                    "name": "create_file",
                    "input": {
                        "path": path,
                        "contentLength": len(content),
                        "preview": summarize_text(content, 200),
                    },
                },
                event_id=tool_event_id,
            )
            started_tool_ids.add(tool_event_id)

        last_len = streamed_lengths.get(tool_event_id, 0)
        if last_len == 0 and content:
            streamed_lengths[tool_event_id] = len(content)
            await self._send("setCode", content)
            self._mark_preview_length(tool_event_id, len(content))
        elif len(content) - last_len >= 40:
            streamed_lengths[tool_event_id] = len(content)
            await self._send("setCode", content)
            self._mark_preview_length(tool_event_id, len(content))