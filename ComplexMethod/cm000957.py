def _flush_unresolved_tool_calls(self, responses: list[StreamBaseResponse]) -> None:
        """Emit outputs for tool calls that didn't receive a UserMessage result.

        SDK built-in tools (WebSearch, Read, etc.) may be executed by the CLI
        internally without surfacing a separate ``UserMessage`` with
        ``ToolResultBlock`` content.  The ``PostToolUse`` hook stashes their
        output, which we pop and emit here before the next ``AssistantMessage``
        starts.
        """
        unresolved = [
            (tid, info.get("name", "unknown"))
            for tid, info in self.current_tool_calls.items()
            if tid not in self.resolved_tool_calls
        ]
        sid = (self.session_id or "?")[:12]
        if not unresolved:
            logger.info(
                "[SDK] [%s] Flush called but all %d tool(s) already resolved",
                sid,
                len(self.current_tool_calls),
            )
            return
        logger.info(
            "[SDK] [%s] Flushing %d unresolved tool call(s): %s",
            sid,
            len(unresolved),
            ", ".join(f"{name}({tid[:12]})" for tid, name in unresolved),
        )

        flushed = False
        for tool_id, tool_name in unresolved:
            output = pop_pending_tool_output(tool_name)
            if output is not None:
                responses.append(
                    StreamToolOutputAvailable(
                        toolCallId=tool_id,
                        toolName=tool_name,
                        output=output,
                        success=True,
                    )
                )
                self.resolved_tool_calls.add(tool_id)
                flushed = True
                logger.info(
                    "[SDK] [%s] Flushed stashed output for %s (call %s, %d chars)",
                    sid,
                    tool_name,
                    tool_id[:12],
                    len(output),
                )
            else:
                # No output available — emit an empty output so the frontend
                # transitions the tool from input-available to output-available
                # (stops the spinner).
                responses.append(
                    StreamToolOutputAvailable(
                        toolCallId=tool_id,
                        toolName=tool_name,
                        output="",
                        success=True,
                    )
                )
                self.resolved_tool_calls.add(tool_id)
                flushed = True
                logger.warning(
                    "[SDK] [%s] Flushed EMPTY output for unresolved tool %s "
                    "(call %s) — stash was empty (likely SDK hook race "
                    "condition: PostToolUse hook hadn't completed before "
                    "flush was triggered)",
                    sid,
                    tool_name,
                    tool_id[:12],
                )

        if flushed:
            # Mirror the UserMessage tool_result path: a flushed tool output is
            # still a tool_result as far as the thinking-only-final-turn guard
            # is concerned.  Without this, a turn whose ONLY tool outputs come
            # from the flush path (SDK built-ins like WebSearch) would miss
            # the fallback synthesis if the model then produced no text.
            self._text_since_last_tool_result = False
            self._any_tool_results_seen = True
            if self.step_open:
                responses.append(StreamFinishStep())
                self.step_open = False