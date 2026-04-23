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
        if not self._tools_enabled(request):
            return DeltaMessage(content=delta_text) if delta_text else None

        content = self._extract_content(current_text)
        regions = self._extract_tool_call_regions(current_text)
        tool_call_deltas: list[DeltaToolCall] = []

        for i, (inner_text, is_complete) in enumerate(regions):
            self._ensure_tool_state_for(i)

            # Extract tool name
            tool_name = self._extract_tool_name_from_region(inner_text)
            if not tool_name:
                break

            # Emit tool name (once per tool call)
            if "name" not in self.prev_tool_call_arr[i]:
                self.prev_tool_call_arr[i]["name"] = tool_name
                tool_call_deltas.append(
                    DeltaToolCall(
                        index=i,
                        id=self._tool_call_ids[i],
                        type="function",
                        function=DeltaFunctionCall(
                            name=tool_name,
                            arguments="",
                        ).model_dump(exclude_none=True),
                    )
                )

            # Build args JSON so far, diff, emit
            args_so_far = self._build_args_json_so_far(
                tool_name, inner_text, is_complete
            )
            diff = self._compute_args_diff(i, args_so_far)
            if diff:
                tool_call_deltas.append(
                    DeltaToolCall(
                        index=i,
                        function=DeltaFunctionCall(arguments=diff).model_dump(
                            exclude_none=True
                        ),
                    )
                )

        # Update current_tool_id for serving layer compatibility
        if regions:
            self.current_tool_id = len(regions) - 1

        if content or tool_call_deltas:
            return DeltaMessage(
                content=content,
                tool_calls=tool_call_deltas,
            )
        return None