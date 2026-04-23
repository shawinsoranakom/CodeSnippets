async def _run_with_session(self, session: ProviderSession) -> str:
        max_steps = 20

        for _ in range(max_steps):
            assistant_event_id = self._next_event_id("assistant")
            thinking_event_id = self._next_event_id("thinking")
            started_tool_ids: set[str] = set()
            streamed_lengths: Dict[str, int] = {}

            async def on_event(event: StreamEvent) -> None:
                if event.type == "assistant_delta":
                    if event.text:
                        await self._send(
                            "assistant",
                            event.text,
                            event_id=assistant_event_id,
                        )
                    return

                if event.type == "thinking_delta":
                    if event.text:
                        await self._send(
                            "thinking",
                            event.text,
                            event_id=thinking_event_id,
                        )
                    return

                if event.type == "tool_call_delta":
                    await self._handle_streamed_tool_delta(
                        event,
                        started_tool_ids,
                        streamed_lengths,
                    )

            turn = await session.stream_turn(on_event)

            if not turn.tool_calls:
                return await self._finalize_response(turn.assistant_text)

            executed_tool_calls: List[ExecutedToolCall] = []
            for tool_call in turn.tool_calls:
                tool_event_id = tool_call.id or self._next_event_id("tool")
                if tool_event_id not in started_tool_ids:
                    await self._send(
                        "toolStart",
                        data={
                            "name": tool_call.name,
                            "input": summarize_tool_input(tool_call, self.file_state),
                        },
                        event_id=tool_event_id,
                    )

                if tool_call.name == "create_file":
                    content = extract_content_from_args(tool_call.arguments)
                    if content:
                        await self._stream_code_preview(tool_event_id, content)

                tool_result = await self.tool_runtime.execute(tool_call)
                if tool_result.updated_content:
                    await self._send("setCode", tool_result.updated_content)

                await self._send(
                    "toolResult",
                    data={
                        "name": tool_call.name,
                        "output": tool_result.summary,
                        "ok": tool_result.ok,
                    },
                    event_id=tool_event_id,
                )
                executed_tool_calls.append(
                    ExecutedToolCall(tool_call=tool_call, result=tool_result)
                )

            session.append_tool_results(turn, executed_tool_calls)

        raise Exception("Agent exceeded max tool turns")