def extract_tool_calls_streaming(
        self,
        previous_text: str,
        current_text: str,
        delta_text: str,
        previous_token_ids: Sequence[int],
        current_token_ids: Sequence[int],
        delta_token_ids: Sequence[int],
        request: ChatCompletionRequest,
    ) -> DeltaMessage | None:
        # The main loop processes the stream from the last known position.
        while True:
            if self.position >= len(current_text):
                return None  # We've processed the entire stream.

            unprocessed_text = current_text[self.position :]

            # STATE: After all tools are done, all subsequent text is content.
            if self.tool_block_finished:
                self.position = len(current_text)
                return DeltaMessage(content=unprocessed_text)

            # STATE: Before the tool block has started.
            if not self.tool_block_started:
                if unprocessed_text.startswith(self.TOOL_CALLS_BEGIN):
                    self.position += len(self.TOOL_CALLS_BEGIN)
                    self.tool_block_started = True
                    continue  # Token consumed, re-loop.

                start_pos = unprocessed_text.find(self.TOOL_CALLS_BEGIN)
                if start_pos == -1:
                    if (
                        self.TOOL_CALLS_BEGIN.startswith(unprocessed_text.strip())
                        and unprocessed_text
                    ):
                        return None  # It's a prefix, wait.
                    self.position = len(current_text)
                    return DeltaMessage(content=unprocessed_text)
                else:
                    content = unprocessed_text[:start_pos]
                    self.position += len(content)
                    return DeltaMessage(content=content)

            # STATE: Inside the main tool block.
            offset = len(unprocessed_text) - len(unprocessed_text.lstrip())
            unprocessed_text = unprocessed_text.lstrip()
            self.position += offset

            if unprocessed_text.startswith(self.TOOL_CALLS_END):
                self.position += len(self.TOOL_CALLS_END)
                self.tool_block_finished = True
                self.current_tool_id = -1
                continue

            # Check if we are between tool calls.
            tool_finished = self.current_tool_id != -1 and self.prev_tool_call_arr[
                self.current_tool_id
            ].get("finished")
            if self.current_tool_id == -1 or tool_finished:
                if unprocessed_text.startswith(self.TOOL_CALL_BEGIN):
                    self.position += len(self.TOOL_CALL_BEGIN)
                    if self.current_tool_id == -1:
                        self.current_tool_id = 0
                    else:
                        self.current_tool_id += 1
                    self.current_tool_name_sent = False
                    while len(self.prev_tool_call_arr) <= self.current_tool_id:
                        self.prev_tool_call_arr.append({})
                    self.prev_tool_call_arr[self.current_tool_id]["finished"] = False
                    continue

                if self.TOOL_CALL_BEGIN.startswith(unprocessed_text):
                    return None

            # STATE: Parsing an active tool call.
            if self.current_tool_id != -1 and not self.prev_tool_call_arr[
                self.current_tool_id
            ].get("finished", False):
                end_tool_pos = unprocessed_text.find(self.TOOL_CALL_END)
                if end_tool_pos == -1:
                    tool_body = unprocessed_text
                else:
                    tool_body = unprocessed_text[:end_tool_pos]

                if end_tool_pos == -1 and self.TOOL_CALL_END.startswith(tool_body):
                    return None

                function_name, arguments = self._parse_steptml_invoke(tool_body)
                if not function_name:
                    return None

                tool_call_arr = {"name": function_name, "parameters": arguments or {}}

                # Send the function name as soon as it's parsed.
                if not self.current_tool_name_sent:
                    self.current_tool_name_sent = True
                    self.prev_tool_call_arr[self.current_tool_id].update(tool_call_arr)
                    return DeltaMessage(
                        tool_calls=[
                            DeltaToolCall(
                                index=self.current_tool_id,
                                type="function",
                                id=f"chatcmpl-tool-{random_uuid()}",
                                function=DeltaFunctionCall(name=function_name),
                            )
                        ]
                    )

                # Update our internal state with the latest parsed arguments.
                self.prev_tool_call_arr[self.current_tool_id].update(  # noqa: E501
                    tool_call_arr
                )

                # Only send arguments when the tool call is complete.
                if end_tool_pos != -1:
                    self.position += end_tool_pos + len(self.TOOL_CALL_END)
                    self.prev_tool_call_arr[self.current_tool_id]["finished"] = True

                    final_args = self._cast_arguments(
                        function_name,
                        tool_call_arr.get("parameters", {}),  # type: ignore
                    )
                    if final_args:
                        final_args_json = json.dumps(final_args, ensure_ascii=False)
                        return DeltaMessage(
                            tool_calls=[
                                DeltaToolCall(
                                    index=self.current_tool_id,
                                    function=DeltaFunctionCall(
                                        arguments=final_args_json
                                    ),
                                )
                            ]
                        )

                # If tool is not finished, return None to wait for more tokens.
                return None

            return None