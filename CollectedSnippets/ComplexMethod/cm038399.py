def extract_tool_calls(
        self,
        model_output: str,
        request: ChatCompletionRequest,
    ) -> ExtractedToolCallInformation:
        msg = ExtractedToolCallInformation(
            tools_called=False, tool_calls=[], content=model_output
        )
        try:
            delimiters = [("TC_START", self.tc_start), ("TC_END", self.tc_end)]
            pattern = "|".join(f"(?P<{name}>{pattern})" for name, pattern in delimiters)
            regex = re.compile(pattern)

            text_segments = list[str]()
            tc_segments = list[str]()
            last_cut_loc = 0

            for match in regex.finditer(model_output):
                match_type = match.lastgroup
                if match_type == "TC_START":
                    assert not self.in_tc, "Two tool call start tokens found in a row"
                    if preceding_text := model_output[last_cut_loc : match.start()]:
                        text_segments.append(preceding_text)
                    self.in_tc = True
                elif match_type == "TC_END":
                    assert self.in_tc, (
                        "Tool call end token found without corresponding start token"
                    )
                    tool_text = model_output[last_cut_loc : match.start()]
                    assert tool_text, (
                        "Expected the model to generate text between tool call tokens"
                    )
                    tc_segments.append(tool_text)
                    self.in_tc = False
                else:
                    raise ValueError("Unexpected match")
                last_cut_loc = match.end()
            assert not self.in_tc, "The model generated an incomplete tool call"
            if final_text := model_output[last_cut_loc:]:
                text_segments.append(final_text)

            content, tool_call_funcs = self._collect_results(
                text_segments, tc_segments, FunctionCall
            )
            tool_calls = [
                ToolCall(
                    type="function",
                    function=func,
                )
                for func in tool_call_funcs
            ]
            msg.tools_called = bool(tool_calls)
            msg.tool_calls = tool_calls
            msg.content = content or None
        except Exception:
            logger.exception("Error in extracting tool call from response.")
        return msg