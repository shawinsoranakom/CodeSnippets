def _handle_tool_args_streaming(
        self, tool_content: str, tool_count: int
    ) -> DeltaMessage | None:
        """
        Handle streaming of tool arguments.

        Args:
            tool_content: Content containing tool calls
            tool_count: Total number of tools

        Returns:
            DeltaMessage with tool arguments or None if no arguments to stream
        """
        current_idx = self._get_current_tool_index()

        if current_idx < 0 or current_idx >= tool_count:
            return None

        tool_name, tool_args = self._get_current_tool_content(tool_content, current_idx)
        if not tool_name or tool_args is None:
            return None

        sent_tools = list(self.streaming_state["sent_tools"])

        if not sent_tools[current_idx]["sent_name"]:
            return None

        clean_args = self._clean_duplicate_braces(tool_args)
        sent_args = sent_tools[current_idx]["sent_arguments"]

        if clean_args != sent_args:
            if sent_args and clean_args.startswith(sent_args):
                args_delta = extract_intermediate_diff(clean_args, sent_args)
                if args_delta:
                    args_delta = self._clean_delta_braces(args_delta)
                    sent_tools[current_idx]["sent_arguments"] = clean_args
                    self.streaming_state["sent_tools"] = sent_tools

                    if clean_args.endswith("}"):
                        self._advance_to_next_tool()

                    return DeltaMessage(
                        tool_calls=[
                            DeltaToolCall(
                                index=current_idx,
                                function=DeltaFunctionCall(
                                    arguments=args_delta
                                ).model_dump(exclude_none=True),
                            )
                        ]
                    )
            elif not sent_args and clean_args:
                clean_args_delta = self._clean_delta_braces(clean_args)
                sent_tools[current_idx]["sent_arguments"] = clean_args
                self.streaming_state["sent_tools"] = sent_tools

                if clean_args.endswith("}"):
                    self._advance_to_next_tool()

                return DeltaMessage(
                    tool_calls=[
                        DeltaToolCall(
                            index=current_idx,
                            function=DeltaFunctionCall(
                                arguments=clean_args_delta
                            ).model_dump(exclude_none=True),
                        )
                    ]
                )

        return None