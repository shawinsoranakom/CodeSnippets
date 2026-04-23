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
            done = False
            text_segments = list[str]()
            tc_segments = list[str]()

            while not done:
                delta_text = self.look_ahead + delta_text
                self.look_ahead = ""
                done, content, tc_text = self._tool_extraction_step(delta_text)
                if content:
                    text_segments.append(content)
                if tc_text:
                    tc_segments.append(tc_text)
                delta_text = ""

            content, tool_call_funcs = self._collect_results(
                text_segments, tc_segments, DeltaFunctionCall
            )

            delta_tool_calls = list[DeltaToolCall]()
            for function in tool_call_funcs:
                self.current_tool_id += 1
                delta_tool_calls.append(
                    DeltaToolCall(
                        id=make_tool_call_id(),
                        type="function",
                        index=self.current_tool_id,
                        function=function.model_dump(exclude_none=True),
                    )
                )
                self.streamed_args_for_tool.append(function.arguments or "")

            assert self.current_tool_id + 1 == len(self.prev_tool_call_arr)
            assert self.current_tool_id + 1 == len(self.streamed_args_for_tool)

            msg = DeltaMessage(content=content or None, tool_calls=delta_tool_calls)
            if msg.content or msg.tool_calls:
                return msg

        except Exception:
            logger.exception("Error trying to handle streaming tool call.")
        return None