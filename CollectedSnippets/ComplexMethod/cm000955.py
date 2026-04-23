def convert_message(self, sdk_message: Message) -> list[StreamBaseResponse]:
        """Convert a single SDK message to Vercel AI SDK format."""
        responses: list[StreamBaseResponse] = []

        if isinstance(sdk_message, SystemMessage):
            if sdk_message.subtype == "init":
                responses.append(
                    StreamStart(messageId=self.message_id, sessionId=self.session_id)
                )
                # Open the first step (matches non-SDK: StreamStart then StreamStartStep)
                responses.append(StreamStartStep())
                self.step_open = True
            elif sdk_message.subtype == "task_progress":
                # Emit a heartbeat so publish_chunk is called during long
                # sub-agent runs. Without this, the Redis stream and meta
                # key TTLs expire during gaps where no real chunks are
                # produced (task_progress events were previously silent).
                responses.append(StreamHeartbeat())

        elif isinstance(sdk_message, StreamEvent):
            # Raw Anthropic streaming events — only delivered when
            # ``include_partial_messages=True`` is set on
            # ``ClaudeAgentOptions`` (gated by
            # ``config.sdk_include_partial_messages``).  Drives per-token
            # emission of text + thinking; tool_use and other structural
            # events stay on the ``AssistantMessage`` path.
            self._handle_stream_event(sdk_message, responses)

        elif isinstance(sdk_message, AssistantMessage):
            # Flush any SDK built-in tool calls that didn't get a UserMessage
            # result (e.g. WebSearch, Read handled internally by the CLI).
            # BUT skip flush when this AssistantMessage is a parallel tool
            # continuation (contains only ToolUseBlocks) — the prior tools
            # are still executing concurrently and haven't finished yet.
            is_tool_only = all(isinstance(b, ToolUseBlock) for b in sdk_message.content)
            if not is_tool_only:
                self._flush_unresolved_tool_calls(responses)

            # After tool results, the SDK sends a new AssistantMessage for the
            # next LLM turn. Open a new step if the previous one was closed.
            if not self.step_open:
                responses.append(StreamStartStep())
                self.step_open = True

            # Hoist ThinkingBlocks to the front of the iteration so the UI
            # sees reasoning *before* the answer it produced — that's the
            # natural reading order and the way Anthropic models emit them.
            # OpenRouter passthrough providers (Moonshot/Kimi, DeepSeek)
            # often place ``reasoning`` after the visible text in the
            # response, which would make ``ReasoningCollapse`` render under
            # the assistant message instead of above it.  ToolUse and other
            # block types stay in their original relative order so tool
            # call sequences remain coherent.
            #
            # Note: when ``include_partial_messages=True`` is active the
            # per-token stream already emitted reasoning + text in their
            # natural on-the-wire order via ``_handle_stream_event``.  The
            # summary walk below falls through to ``_emit_text_tail`` /
            # ``_emit_thinking_tail`` which emit only the diff, preserving
            # that ordering without duplicating content.
            blocks_with_idx = sorted(
                enumerate(sdk_message.content),
                key=lambda pair: 0 if isinstance(pair[1], ThinkingBlock) else 1,
            )

            for block_index, block in blocks_with_idx:
                if isinstance(block, TextBlock):
                    # Reasoning and text are distinct UI parts; close any
                    # open reasoning block before opening text so the AI
                    # SDK transport doesn't merge them.
                    tail = self._text_tail_for_summary_block(block.text)
                    if tail:
                        self._end_reasoning_if_open(responses)
                        self._ensure_text_started(responses)
                        responses.append(
                            StreamTextDelta(id=self.text_block_id, delta=tail)
                        )
                        self._text_since_last_tool_result = True
                    elif block.text:
                        # Partial stream already emitted the full text.
                        self._text_since_last_tool_result = True

                elif isinstance(block, ThinkingBlock):
                    # Stream extended_thinking content as a reasoning
                    # block.  The Vercel AI SDK's ``useChat`` transport
                    # recognises ``reasoning-start`` / ``reasoning-delta``
                    # / ``reasoning-end`` events and accumulates them into
                    # a ``type: 'reasoning'`` UIMessage part the frontend
                    # renders via ``ReasoningCollapse`` (collapsed by
                    # default).  We also persist the text as a
                    # ``type: 'thinking'`` part in ``session.messages`` via
                    # ``_format_sdk_content_blocks``, so shared / reloaded
                    # sessions see the same reasoning.  Without streaming
                    # it live, extended_thinking turns that end
                    # thinking-only left the UI stuck on "Thought for Xs"
                    # with nothing rendered until a page refresh.
                    #
                    # When ``render_reasoning_in_ui=False`` the three
                    # reasoning helpers below (and the append) no-op, so
                    # the frontend sees a text-only stream AND no
                    # ``ChatMessage(role='reasoning')`` row is persisted
                    # (the row is only created by ``_dispatch_response``
                    # when ``StreamReasoningStart`` arrives, which is
                    # suppressed here).  Persistence of the thinking text
                    # into the SDK transcript via
                    # ``_format_sdk_content_blocks`` is unaffected — that
                    # feeds ``--resume`` continuity, not the UI.
                    #
                    # Flush any pending coalesce buffer to the wire BEFORE
                    # computing the tail — otherwise a summary that
                    # arrives between the last partial delta and the
                    # ``content_block_stop`` event (race: summary is
                    # flushed by the CLI as soon as the block is complete
                    # provider-side, with stop lagging as a separate
                    # frame) would see ``_partial_thinking_buffer``
                    # missing the pending prefix, and
                    # ``_thinking_tail_for_summary_block`` would emit the
                    # full block — duplicating the tail that
                    # ``_end_reasoning_if_open`` still drains on stop.
                    self._flush_pending_thinking(responses)
                    tail = self._thinking_tail_for_summary_block(block.thinking)
                    if tail:
                        self._end_text_if_open(responses)
                        self._ensure_reasoning_started(responses)
                        responses.append(
                            StreamReasoningDelta(
                                id=self.reasoning_block_id,
                                delta=tail,
                            )
                        )

                elif isinstance(block, ToolUseBlock):
                    self._end_text_if_open(responses)
                    self._end_reasoning_if_open(responses)

                    # Strip MCP prefix so frontend sees "find_block"
                    # instead of "mcp__copilot__find_block".
                    tool_name = block.name.strip().removeprefix(MCP_TOOL_PREFIX)

                    responses.append(
                        StreamToolInputStart(toolCallId=block.id, toolName=tool_name)
                    )
                    responses.append(
                        StreamToolInputAvailable(
                            toolCallId=block.id,
                            toolName=tool_name,
                            input=block.input,
                        )
                    )
                    self.current_tool_calls[block.id] = {"name": tool_name}

        elif isinstance(sdk_message, UserMessage):
            # UserMessage carries tool results back from tool execution.
            content = sdk_message.content
            blocks = content if isinstance(content, list) else []
            resolved_in_blocks: set[str] = set()

            sid = (self.session_id or "?")[:12]
            parent_id_preview = getattr(sdk_message, "parent_tool_use_id", None)
            logger.info(
                "[SDK] [%s] UserMessage: %d blocks, content_type=%s, "
                "parent_tool_use_id=%s",
                sid,
                len(blocks),
                type(content).__name__,
                parent_id_preview[:12] if parent_id_preview else "None",
            )

            for block in blocks:
                if isinstance(block, ToolResultBlock) and block.tool_use_id:
                    # Skip if already resolved (e.g. by flush) — the real
                    # result supersedes the empty flush, but re-emitting
                    # would confuse the frontend's state machine.
                    if block.tool_use_id in self.resolved_tool_calls:
                        continue
                    tool_info = self.current_tool_calls.get(block.tool_use_id, {})
                    tool_name = tool_info.get("name", "unknown")

                    # Prefer the stashed full output over the SDK's
                    # (potentially truncated) ToolResultBlock content.
                    # The SDK truncates large results, writing them to disk,
                    # which breaks frontend widget parsing.
                    output = pop_pending_tool_output(tool_name) or (
                        _extract_tool_output(block.content)
                    )

                    responses.append(
                        StreamToolOutputAvailable(
                            toolCallId=block.tool_use_id,
                            toolName=tool_name,
                            output=output,
                            success=not (block.is_error or False),
                        )
                    )
                    resolved_in_blocks.add(block.tool_use_id)

            # Handle SDK built-in tool results carried via parent_tool_use_id
            # instead of (or in addition to) ToolResultBlock content.
            parent_id = sdk_message.parent_tool_use_id
            if (
                parent_id
                and parent_id not in resolved_in_blocks
                and parent_id not in self.resolved_tool_calls
            ):
                tool_info = self.current_tool_calls.get(parent_id, {})
                tool_name = tool_info.get("name", "unknown")

                # Try stashed output first (from PostToolUse hook),
                # then tool_use_result dict, then string content.
                output = pop_pending_tool_output(tool_name)
                if not output:
                    tur = sdk_message.tool_use_result
                    if tur is not None:
                        output = _extract_tool_use_result(tur)
                if not output and isinstance(content, str) and content.strip():
                    output = content.strip()

                if output:
                    responses.append(
                        StreamToolOutputAvailable(
                            toolCallId=parent_id,
                            toolName=tool_name,
                            output=output,
                            success=True,
                        )
                    )
                    resolved_in_blocks.add(parent_id)

            self.resolved_tool_calls.update(resolved_in_blocks)
            if resolved_in_blocks:
                # A new tool_result just landed — reset the
                # "has the model emitted text since the last tool result?"
                # tracker so the thinking-only-final-turn guard at
                # ``ResultMessage`` time stays accurate.
                self._text_since_last_tool_result = False
                self._any_tool_results_seen = True

            # Close the current step after tool results — the next
            # AssistantMessage will open a new step for the continuation.
            if self.step_open:
                self._end_reasoning_if_open(responses)
                responses.append(StreamFinishStep())
                self.step_open = False

        elif isinstance(sdk_message, ResultMessage):
            self._flush_unresolved_tool_calls(responses)
            # Thinking-only final turn guard: when the model's last LLM
            # call after a tool result produced only a ``ThinkingBlock``
            # (no ``TextBlock``, no ``ToolUseBlock``) the UI has nothing
            # to render after the tool output — it hangs on "Thought for
            # Xs" with no response text.  Synthesise a short closing line
            # so the turn visibly completes.  Condition: we've seen at
            # least one tool_result AND zero TextBlocks since.  The
            # prompt rule (``_USER_FOLLOW_UP_NOTE``'s closing clause)
            # asks the model to always end with text, but we can't rely
            # on it for extended_thinking / edge cases.
            if (
                self._any_tool_results_seen
                and not self._text_since_last_tool_result
                and sdk_message.subtype == "success"
            ):
                # UserMessage (tool_result) closed the last step, so we must
                # open a fresh one before emitting any text — the AI SDK v5
                # transport rejects text-delta chunks that aren't wrapped in
                # start-step / finish-step.
                if not self.step_open:
                    responses.append(StreamStartStep())
                    self.step_open = True
                # Close any open reasoning block first — text and reasoning
                # must not interleave on the wire (AI SDK v5 maps distinct
                # start/end events to distinct UI parts).
                self._end_reasoning_if_open(responses)
                self._ensure_text_started(responses)
                responses.append(
                    StreamTextDelta(
                        id=self.text_block_id,
                        delta="(Done — no further commentary.)",
                    )
                )
            self._end_text_if_open(responses)
            self._end_reasoning_if_open(responses)
            # Close the step before finishing.
            if self.step_open:
                responses.append(StreamFinishStep())
                self.step_open = False

            if sdk_message.subtype == "success":
                responses.append(StreamFinish())
            elif sdk_message.subtype in ("error", "error_during_execution"):
                raw_error = str(sdk_message.result or "Unknown error")
                if is_transient_api_error(raw_error):
                    error_text, code = FRIENDLY_TRANSIENT_MSG, "transient_api_error"
                else:
                    error_text, code = raw_error, "sdk_error"
                responses.append(StreamError(errorText=error_text, code=code))
                responses.append(StreamFinish())
            else:
                logger.warning(
                    f"Unexpected ResultMessage subtype: {sdk_message.subtype}"
                )
                responses.append(StreamFinish())

        else:
            logger.debug(f"Unhandled SDK message type: {type(sdk_message).__name__}")

        return responses