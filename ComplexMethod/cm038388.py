def _extract_tool_calls_streaming(
        self,
        delta_text: str,
        delta_token_ids: Sequence[int],
    ) -> DeltaMessage | None:
        """
        Extracts tool calls for Mistral models
        doing tool calls of the following format:
        `[TOOL_CALLS]add{"a": 3.5, "b": 4}`
        """
        additional_content: str = ""
        if self.streaming_state == StreamingState.WAITING_FOR_TOOL_START:
            # this is the first tool call
            if self.bot_token not in delta_text:
                return DeltaMessage(content=delta_text)
            if not delta_text.startswith(self.bot_token):
                additional_content += delta_text.split(self.bot_token)[0]
                delta_text = self.bot_token + "".join(
                    delta_text.split(self.bot_token)[1:]
                )

        delta_tool_calls = self._generate_delta_tool_call(delta_text)
        if not additional_content and len(delta_tool_calls) == 0:
            if self.streaming_state in [
                StreamingState.PARSING_ARGUMENTS,
                StreamingState.PARSING_ARGUMENTS_COMPLETED,
                StreamingState.TOOL_COMPLETE,
                StreamingState.ALL_TOOLS_COMPLETE,
            ]:
                # Return an empty DeltaMessage once the tool calls are all done
                # so that finish_reason gets set.
                return DeltaMessage()
            else:
                # return None when the tool is not likely to be finished
                # This can occur when the name is being parsed for example
                # and we wait for the name to be complete
                # before sending the function name
                return None

        delta = DeltaMessage()
        if additional_content:
            delta.content = additional_content
        if len(delta_tool_calls) > 0:
            delta.tool_calls = delta_tool_calls

        # HACK: serving_chat.py inspects the internal state of tool parsers
        # when determining its final streaming delta, automatically
        # adding autocompleted JSON.
        # These two lines avoid that nonsense while ensuring finish_reason
        # is set to tool_calls when at least one tool is called.
        if delta_tool_calls and not self.prev_tool_call_arr:
            self.prev_tool_call_arr = [{"arguments": {}}]
        return delta