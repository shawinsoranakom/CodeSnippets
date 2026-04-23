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
        try:
            # Extract any content before tool calls.
            content = self._extract_content(current_text)
            tool_calls = self._extract_tool_calls(current_text)
            tool_call_deltas: list[DeltaToolCall] = []

            for i, tool_call in enumerate(tool_calls):
                # First time seeing tool call at index i.
                if i >= len(self.prev_tool_call_arr):
                    # Initialize streaming state.
                    self.prev_tool_call_arr.append({})
                    self.streamed_args_for_tool.append("")

                header, tool_args = self._split_tool_call(tool_call)

                # Stream back tool name.
                if "name" not in self.prev_tool_call_arr[i]:
                    tool_id, tool_name = self._extract_tool_id_and_name(header)
                    if not tool_name:
                        # Can't skip to tool i+1 if i isn't ready
                        break
                    self.prev_tool_call_arr[i]["name"] = tool_name
                    self.prev_tool_call_arr[i]["id"] = tool_id
                    tool_call_deltas.append(
                        DeltaToolCall(
                            index=i,
                            type="function",
                            id=tool_id,
                            function=DeltaFunctionCall(name=tool_name).model_dump(
                                exclude_none=True
                            ),
                        )
                    )

                # Stream back new tool args by diffing against what was sent.
                args_diff = self._compute_args_diff(i, tool_args)
                if args_diff:
                    tool_call_deltas.append(
                        DeltaToolCall(
                            index=i,
                            function=DeltaFunctionCall(arguments=args_diff).model_dump(
                                exclude_none=True
                            ),
                        )
                    )

            if content or tool_call_deltas:
                return DeltaMessage(
                    content=content,
                    tool_calls=tool_call_deltas,
                )
            return None

        except Exception:
            logger.exception("Error trying to handle streaming tool call.")
            return None