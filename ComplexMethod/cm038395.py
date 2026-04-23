def extract_tool_calls(
        self,
        model_output: str,
        request: ChatCompletionRequest,
    ) -> ExtractedToolCallInformation:
        matched_tool_calls = self.func_call_regex.findall(model_output)
        logger.debug("model_output: %s", model_output)
        try:
            tool_calls: list[ToolCall] = []
            for match in matched_tool_calls:
                tc_detail = self.func_detail_regex.search(match)
                if not tc_detail:
                    logger.warning(
                        "Failed to parse tool call details from: %s",
                        match,
                    )
                    continue
                tc_name = tc_detail.group(1).strip()
                tc_args = tc_detail.group(2)
                pairs = self.func_arg_regex.findall(tc_args) if tc_args else []
                arg_dct: dict[str, Any] = {}
                for key, value in pairs:
                    arg_key = key.strip()
                    arg_val = value.strip()
                    if not self._is_string_type(tc_name, arg_key, self.tools):
                        arg_val = self._deserialize(arg_val)
                    logger.debug("arg_key = %s, arg_val = %s", arg_key, arg_val)
                    arg_dct[arg_key] = arg_val
                tool_calls.append(
                    ToolCall(
                        type="function",
                        function=FunctionCall(
                            name=tc_name,
                            arguments=json.dumps(arg_dct, ensure_ascii=False),
                        ),
                    )
                )
        except Exception:
            logger.exception("Failed to extract tool call spec")
            return ExtractedToolCallInformation(
                tools_called=False, tool_calls=[], content=model_output
            )
        else:
            if len(tool_calls) > 0:
                content: str | None = model_output[
                    : model_output.find(self.tool_calls_start_token)
                ]
                # Normalize empty/whitespace-only content to None
                if not content or not content.strip():
                    content = None
                return ExtractedToolCallInformation(
                    tools_called=True, tool_calls=tool_calls, content=content
                )
            return ExtractedToolCallInformation(
                tools_called=False, tool_calls=[], content=model_output
            )