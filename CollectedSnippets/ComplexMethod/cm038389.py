def _generate_delta_tool_call(self, delta_text: str) -> list[DeltaToolCall]:
        if delta_text == "" or delta_text is None:
            return []
        delta_function_name = None
        tool_id = None
        if self.streaming_state not in [
            StreamingState.PARSING_NAME,
            StreamingState.PARSING_ARGUMENTS,
        ] and delta_text.startswith(self.bot_token):
            self.current_tool_id += 1
            self.streaming_state = StreamingState.PARSING_NAME
            delta_text = delta_text.replace(self.bot_token, "", 1)
        if self.streaming_state == StreamingState.PARSING_NAME:
            if self.current_tool_name is None:
                self.current_tool_name = ""
            # The name stops where the arguments start
            # And the arguments start with the `{` char
            if "{" in delta_text:
                tool_id = MistralToolCall.generate_random_id()
                delta_function_name = delta_text.split("{")[0]
                self.current_tool_name += delta_function_name
                delta_text = delta_text[len(delta_function_name) :]
                self.streaming_state = StreamingState.PARSING_ARGUMENTS
            else:
                # we want to send the tool name once it's complete
                self.current_tool_name += delta_text
                return []
        if self.streaming_state == StreamingState.PARSING_ARGUMENTS:
            next_function_text = None
            if self.bot_token in delta_text:
                # current tool call is over
                delta_arguments = ""
                delta_arguments += delta_text.split(self.bot_token)[0]
                next_function_text = delta_text[len(delta_arguments) :]
                self.streaming_state = StreamingState.TOOL_COMPLETE
            else:
                delta_arguments = delta_text
            ret = []
            if self.current_tool_name or delta_arguments:
                ret += [
                    DeltaToolCall(
                        index=self.current_tool_id,
                        type="function",
                        id=tool_id,
                        function=DeltaFunctionCall(
                            name=self.current_tool_name, arguments=delta_arguments
                        ).model_dump(exclude_none=True),
                    )
                ]
                self.current_tool_name = None
            if next_function_text:
                ret += self._generate_delta_tool_call(next_function_text)
            return ret
        # Should not happen
        return []