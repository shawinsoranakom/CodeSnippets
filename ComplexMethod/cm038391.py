def _extract_tool_calls_streaming_pre_v11_tokenizer(
        self,
        delta_text: str,
        delta_token_ids: Sequence[int],
    ) -> DeltaMessage | None:
        """
        Extracts tool calls for Mistral models
        doing tool calls of the following format:
        `[TOOL_CALLS][{"name": "add", "arguments":{"a": 3.5, "b": 4}}`
        """
        assert self.parse_coro is not None
        content = None
        delta_tool_calls: list[DeltaToolCall] = []
        current_tool_call: DeltaToolCall = DeltaToolCall(
            index=self.current_tool_id, type="function"
        )
        current_tool_call_modified = False
        if self.bot_token_id in delta_token_ids or self.bot_token in delta_text:
            # this is the first tool call
            if not delta_text.startswith(self.bot_token):
                content = delta_text.split(self.bot_token)[0]
            delta_text = "".join(delta_text.split(self.bot_token)[1:])

        # Cut smartly the delta text to catch the ijson events
        # as ijson does not give us the index in the text at each event.
        # We need to cut so that we know
        # where in the text the events are emitted from.
        while len(delta_text) > 0:
            streaming_state_before_parse = self.streaming_state

            if self.streaming_state == StreamingState.WAITING_FOR_TOOL_START:
                delta_to_be_parsed, delta_text = self._split_delta(
                    delta_text=delta_text,
                    stop_after_opening_curly_braces=1,
                )
            elif self.streaming_state == StreamingState.WAITING_FOR_TOOL_KEY:
                # Wait until another key is sent
                # or the current tool is completed
                delta_to_be_parsed, delta_text = self._split_delta(
                    delta_text=delta_text,
                    stop_after_colon=1,
                    stop_after_opening_curly_braces=1,
                    # if the tool ends, we want to separate
                    # at the start of the next tool
                )
            elif self.streaming_state == StreamingState.PARSING_NAME:
                delta_to_be_parsed, delta_text = self._split_delta(
                    delta_text=delta_text,
                    stop_after_comma=1,
                    stop_after_closing_brackets=1,
                )
            elif self.streaming_state == StreamingState.WAITING_FOR_ARGUMENTS_START:
                delta_to_be_parsed, delta_text = self._split_delta(
                    delta_text=delta_text,
                    stop_after_opening_curly_braces=1,
                )
            elif self.streaming_state == StreamingState.PARSING_ARGUMENTS:
                delta_to_be_parsed, delta_text = self._split_delta(
                    delta_text=delta_text,
                    stop_after_closing_curly_braces=1,
                    # we could be more clever
                    # by listening to item.arguments.* start_map events
                    # and know how many curly braces we can allow
                )
            elif self.streaming_state in [
                StreamingState.PARSING_ARGUMENTS_COMPLETED,
                StreamingState.PARSING_NAME_COMPLETED,
            ]:
                delta_to_be_parsed, delta_text = self._split_delta(
                    delta_text=delta_text,
                    stop_after_closing_curly_braces=1,
                    stop_after_closing_brackets=1,
                )
            elif self.streaming_state == StreamingState.TOOL_COMPLETE:
                delta_to_be_parsed, delta_text = self._split_delta(
                    delta_text=delta_text,
                    stop_after_opening_curly_braces=1,
                    stop_after_closing_brackets=1,
                )
            elif self.streaming_state == StreamingState.ALL_TOOLS_COMPLETE:
                content = delta_text
                delta_text = ""
            else:
                delta_to_be_parsed = delta_text
                delta_text = ""

            if self.streaming_state != StreamingState.ALL_TOOLS_COMPLETE:
                self.parse_coro.send(delta_to_be_parsed.encode("utf-8"))

            # Given the parsed text and the possible streaming state change,
            # let's add to the tool delta
            if (
                (streaming_state_before_parse != self.streaming_state)
                and streaming_state_before_parse
                in [StreamingState.WAITING_FOR_TOOL_START, StreamingState.TOOL_COMPLETE]
                and self.streaming_state
                not in [
                    StreamingState.ALL_TOOLS_COMPLETE,
                    StreamingState.TOOL_COMPLETE,
                    StreamingState.WAITING_FOR_TOOL_START,
                ]
            ):
                # starting a new tool call
                if current_tool_call_modified:
                    if self.current_tool_mistral_id is not None:
                        current_tool_call.id = self.current_tool_mistral_id
                        self.current_tool_mistral_id = None
                    delta_tool_calls.append(current_tool_call)
                current_tool_call_modified = False
                self.current_tool_id += 1
                self.current_tool_mistral_id = MistralToolCall.generate_random_id()
                current_tool_call = DeltaToolCall(
                    index=self.current_tool_id,
                    type="function",
                )
            if current_tool_call.function is None:
                current_tool_call.function = DeltaFunctionCall()

            if self.current_tool_name is not None:
                # we have the complete tool name
                current_tool_call_modified = True
                current_tool_call.function.name = self.current_tool_name
                self.current_tool_name = None
            if self.streaming_state == StreamingState.PARSING_NAME_COMPLETED:
                self.streaming_state = StreamingState.WAITING_FOR_TOOL_KEY
            if self.streaming_state in [
                StreamingState.PARSING_ARGUMENTS,
                StreamingState.PARSING_ARGUMENTS_COMPLETED,
            ]:
                if self.streaming_state == StreamingState.PARSING_ARGUMENTS_COMPLETED:
                    self.streaming_state = StreamingState.WAITING_FOR_TOOL_KEY
                # the delta_to_be_parsed is part of arguments.
                current_tool_call_modified = True
                if current_tool_call.function.arguments is None:
                    current_tool_call.function.arguments = delta_to_be_parsed
                else:
                    current_tool_call.function.arguments += delta_to_be_parsed
                if streaming_state_before_parse != StreamingState.PARSING_ARGUMENTS:
                    # It's the first chunk of arg. let's lstrip it
                    current_tool_call.function.arguments = (
                        current_tool_call.function.arguments.lstrip()
                    )

        if current_tool_call_modified:
            if self.current_tool_mistral_id is not None:
                current_tool_call.id = self.current_tool_mistral_id
                self.current_tool_mistral_id = None
            delta_tool_calls.append(current_tool_call)

        # HACK: serving_chat.py inspects the internal state of tool parsers
        # when determining it's final streaming delta, automatically
        # adding autocompleted JSON.
        # These two lines avoid that nonsense while ensuring finish_reason
        # is set to tool_calls when at least one tool is called.
        if delta_tool_calls and not self.prev_tool_call_arr:
            self.prev_tool_call_arr = [{"arguments": {}}]

        if content or len(delta_tool_calls) > 0:
            delta_message = DeltaMessage()
            if content:
                delta_message.content = content
            if len(delta_tool_calls) > 0:
                delta_message.tool_calls = delta_tool_calls
            return delta_message
        else:
            if self.streaming_state == StreamingState.ALL_TOOLS_COMPLETE:
                return DeltaMessage()
            else:
                return None