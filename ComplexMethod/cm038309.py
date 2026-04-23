def _handle_tool_args_streaming(
        self, current_text: str, current_idx: int, tool_count: int
    ):
        if current_idx >= 0 and current_idx < tool_count:
            empty_args_match = self.tool_empty_arg_reg.search(current_text)
            if empty_args_match and empty_args_match.start() > 0:
                for i in range(tool_count):
                    if i == current_idx:
                        if not self.streaming_state["sent_tools"][current_idx][
                            "sent_arguments_prefix"
                        ]:
                            self.streaming_state["sent_tools"][current_idx][
                                "sent_arguments_prefix"
                            ] = True
                            self.streaming_state["sent_tools"][current_idx][
                                "sent_arguments"
                            ] = "{}"
                            while len(self.streamed_args) <= current_idx:
                                self.streamed_args.append("")
                            self.streamed_args[current_idx] += "{}"
                            delta = DeltaMessage(
                                tool_calls=[
                                    DeltaToolCall(
                                        index=current_idx,
                                        function=DeltaFunctionCall(
                                            arguments="{}"
                                        ).model_dump(exclude_none=True),
                                    )
                                ]
                            )
                            if current_idx < tool_count - 1:
                                self.streaming_state["current_tool_index"] += 1
                                self.current_tool_id = self.streaming_state[
                                    "current_tool_index"
                                ]
                            return delta

            args_matches = list(self.tool_non_empty_arg_reg.finditer(current_text))
            if current_idx < len(args_matches):
                args_text = args_matches[current_idx].group(1)
                is_last_tool = current_idx == tool_count - 1
                if not is_last_tool:
                    next_tool_pos = current_text.find(
                        "},{", args_matches[current_idx].start()
                    )
                    if next_tool_pos != -1:
                        args_end_pos = next_tool_pos + 1
                        args_text = (
                            current_text[
                                args_matches[current_idx].start() : args_end_pos
                            ]
                            .split('"arguments":')[1]
                            .strip()
                        )
                sent_args = self.streaming_state["sent_tools"][current_idx][
                    "sent_arguments"
                ]
                if not self.streaming_state["sent_tools"][current_idx][
                    "sent_arguments_prefix"
                ] and args_text.startswith("{"):
                    self.streaming_state["sent_tools"][current_idx][
                        "sent_arguments_prefix"
                    ] = True
                    self.streaming_state["sent_tools"][current_idx][
                        "sent_arguments"
                    ] = "{"
                    while len(self.streamed_args) <= current_idx:
                        self.streamed_args.append("")
                    self.streamed_args[current_idx] += "{"
                    delta = DeltaMessage(
                        tool_calls=[
                            DeltaToolCall(
                                index=current_idx,
                                function=DeltaFunctionCall(arguments="{").model_dump(
                                    exclude_none=True
                                ),
                            )
                        ]
                    )
                    return delta

                if args_text.startswith(sent_args):
                    args_diff = args_text[len(sent_args) :]
                    if args_diff:
                        self.streaming_state["sent_tools"][current_idx][
                            "sent_arguments"
                        ] = args_text
                        while len(self.streamed_args) <= current_idx:
                            self.streamed_args.append("")
                        self.streamed_args[current_idx] += args_diff
                        delta = DeltaMessage(
                            tool_calls=[
                                DeltaToolCall(
                                    index=current_idx,
                                    function=DeltaFunctionCall(
                                        arguments=args_diff
                                    ).model_dump(exclude_none=True),
                                )
                            ]
                        )
                        return delta

                if args_text.endswith("}") and args_text == sent_args:
                    if current_idx < tool_count - 1:
                        self.streaming_state["current_tool_index"] += 1
                        self.current_tool_id = self.streaming_state[
                            "current_tool_index"
                        ]
        return None