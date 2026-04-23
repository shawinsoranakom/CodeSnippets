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
        self._buffer += delta_text
        cur_text = self._buffer
        start_idx = cur_text.find(self.tool_call_start_token)
        if start_idx == -1:
            self._buffer = ""
            # At least one toolcall has been completed
            if self.current_tool_id > 0:
                cur_text = ""
            if self.current_tool_id == -1 and all(
                token_id == self.newline_token_id for token_id in previous_token_ids
            ):
                cur_text = cur_text.strip("\n")

            # handle <response> </response> when tool_call is not triggered
            # cur_text === delta_text
            content = cur_text
            if self.response_start_token_id in delta_token_ids:
                content = content.lstrip("\n")
                response_start_idx = content.find(self.response_start_token)
                content = content[response_start_idx + len(self.response_start_token) :]
                # if have </response>, remove it
                response_end_idx = content.rfind(self.response_end_token)
                if response_end_idx != -1:
                    content = content[:response_end_idx]
            elif self.response_end_token_id in delta_token_ids:
                response_end_idx = content.rfind(self.response_end_token)
                content = content[:response_end_idx]
            # remove \n after </think> or <response> or </response>
            if (
                len(previous_token_ids) > 0
                and previous_token_ids[-1] in self.parser_token_ids
            ) and (
                len(delta_token_ids) > 0 and delta_token_ids[0] == self.newline_token_id
            ):
                content = content.lstrip("\n")

            return DeltaMessage(content=content if content else None)
        logger.debug("cur_text = %s", cur_text)
        end_idx = cur_text.find(self.tool_call_end_token)
        if end_idx != -1:
            if self.current_tool_id == -1:
                self.current_tool_id = 0
                self.prev_tool_call_arr = []
                self.streamed_args_for_tool = []
            while len(self.prev_tool_call_arr) <= self.current_tool_id:
                self.prev_tool_call_arr.append({})
            while len(self.streamed_args_for_tool) <= self.current_tool_id:
                self.streamed_args_for_tool.append("")

            extracted_tool_calls = self.extract_tool_calls(
                cur_text[: end_idx + len(self.tool_call_end_token)], request
            )

            if len(extracted_tool_calls.tool_calls) == 0:
                logger.warning("Failed to extract any tool calls.")
                return None
            tool_call = extracted_tool_calls.tool_calls[0]
            self.prev_tool_call_arr[self.current_tool_id] = {
                "name": tool_call.function.name,
                "arguments": json.loads(tool_call.function.arguments),
            }
            self.streamed_args_for_tool[self.current_tool_id] = (
                tool_call.function.arguments
            )
            delta = DeltaMessage(
                content=extracted_tool_calls.content,
                tool_calls=[
                    DeltaToolCall(
                        index=self.current_tool_id,
                        id=tool_call.id,
                        type=tool_call.type,
                        function=DeltaFunctionCall(
                            name=tool_call.function.name,
                            arguments=tool_call.function.arguments,
                        ),
                    )
                ],
            )
            self.current_tool_id += 1
            self._buffer = cur_text[end_idx + len(self.tool_call_end_token) :]
            return delta

        self._buffer = cur_text[start_idx:]
        content = cur_text[:start_idx].rstrip("\n")
        return DeltaMessage(content=content if content else None)