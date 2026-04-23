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
        delta_text = self._buffer_delta_text(delta_text)
        current_text = previous_text + delta_text

        if self.tool_call_start_token not in current_text:
            if delta_text:
                return DeltaMessage(content=delta_text)
            return None

        try:
            start_count = current_text.count(self.tool_call_start_token)
            end_count = current_text.count(self.tool_call_end_token)
            prev_start_count = previous_text.count(self.tool_call_start_token)
            prev_end_count = previous_text.count(self.tool_call_end_token)

            if self.tool_call_start_token not in current_text:
                return DeltaMessage(content=delta_text)

            # Starting a new function call
            if start_count > prev_start_count and start_count > end_count:
                self.current_tool_id += 1
                self.current_tool_name_sent = False
                self.streamed_args_for_tool.append("")
                self.prev_tool_call_arr.append({})
                logger.debug("Starting new tool call %d", self.current_tool_id)
                return None

            # In the middle of a function call
            if start_count > end_count:
                last_start = current_text.rfind(self.tool_call_start_token)
                partial_call = current_text[
                    last_start + len(self.tool_call_start_token) :
                ]

                if partial_call.startswith("call:"):
                    func_part = partial_call[5:]

                    if "{" in func_part:
                        func_name = func_part.split("{")[0]
                        args_part = (
                            func_part.split("{", 1)[1] if "{" in func_part else ""
                        )

                        if not self.current_tool_name_sent and func_name:
                            self.current_tool_name_sent = True
                            self.prev_tool_call_arr[self.current_tool_id] = {
                                "name": func_name,
                                "arguments": {},
                            }
                            return DeltaMessage(
                                tool_calls=[
                                    DeltaToolCall(
                                        index=self.current_tool_id,
                                        type="function",
                                        id=make_tool_call_id(),
                                        function=DeltaFunctionCall(
                                            name=func_name
                                        ).model_dump(exclude_none=True),
                                    )
                                ]
                            )

                        if self.current_tool_name_sent and args_part:
                            current_args = self._parse_arguments(args_part)
                            if current_args:
                                current_args_json = json.dumps(
                                    current_args, ensure_ascii=False
                                )
                                prev_streamed = self.streamed_args_for_tool[
                                    self.current_tool_id
                                ]

                                if len(current_args_json) > len(prev_streamed):
                                    diff = current_args_json[len(prev_streamed) :]
                                    self.streamed_args_for_tool[
                                        self.current_tool_id
                                    ] = current_args_json
                                    self.prev_tool_call_arr[self.current_tool_id][
                                        "arguments"
                                    ] = current_args

                                    return DeltaMessage(
                                        tool_calls=[
                                            DeltaToolCall(
                                                index=self.current_tool_id,
                                                function=DeltaFunctionCall(
                                                    arguments=diff
                                                ).model_dump(exclude_none=True),
                                            )
                                        ]
                                    )

                return None

            # Function call just ended
            if end_count > prev_end_count:
                if self.current_tool_id >= 0 and self.current_tool_id < len(
                    self.prev_tool_call_arr
                ):
                    all_calls = self.tool_call_regex.findall(current_text)
                    args = {}
                    if self.current_tool_id < len(all_calls):
                        match = all_calls[self.current_tool_id]
                        if match[0]:
                            args_str = match[1]
                            args = self._parse_arguments(args_str)
                            self.prev_tool_call_arr[self.current_tool_id][
                                "arguments"
                            ] = args

                    if args:
                        args_json = json.dumps(args, ensure_ascii=False)
                        prev_streamed = self.streamed_args_for_tool[
                            self.current_tool_id
                        ]
                        if len(args_json) > len(prev_streamed):
                            diff = args_json[len(prev_streamed) :]
                            self.streamed_args_for_tool[self.current_tool_id] = (
                                args_json
                            )
                            return DeltaMessage(
                                tool_calls=[
                                    DeltaToolCall(
                                        index=self.current_tool_id,
                                        function=DeltaFunctionCall(
                                            arguments=diff
                                        ).model_dump(exclude_none=True),
                                    )
                                ]
                            )
                return None

            if delta_text:
                return DeltaMessage(content=delta_text)
            return None

        except Exception:
            logger.exception("Error in streaming tool call extraction")
            return None