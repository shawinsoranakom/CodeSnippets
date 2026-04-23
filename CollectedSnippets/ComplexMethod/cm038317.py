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
        content = None
        func_name = None
        cur_args = None
        m_func = REGEX_FUNCTION_CALL.search(current_text)
        if not self.tool_started:
            m_content = REGEX_CONTENT_PATTERN.search(delta_text)
            if m_content:
                content = m_content.group(1)
                self.end_content = True
            else:
                if not self.end_content:
                    content = delta_text
            if m_func:
                self.tool_started = True
            if content:
                return DeltaMessage(content=content)
        if not m_func:
            return None
        json_tail = m_func.group(1).strip()
        name_match = NAME_REGEX.search(json_tail)
        if name_match:
            func_name = name_match.group(1)
        args_match = ARGS_REGEX.search(json_tail)
        if args_match:
            cur_args = args_match.group(1).strip()
            if cur_args.endswith("</s>"):
                cur_args = cur_args[: -len("</s>")]
            if cur_args.endswith("}"):  # last '}' end of json
                try:
                    candidate = cur_args[:-1].strip()
                    json.loads(candidate, strict=False)
                    cur_args = candidate
                except json.JSONDecodeError:
                    pass
        if not self.prev_tool_call_arr:
            self.prev_tool_call_arr.append({})
        if not self.tool_name_sent:
            if not func_name:
                return None
            self.tool_name_sent = True
            self.tool_id = make_tool_call_id()
            self.prev_tool_call_arr[0]["name"] = func_name
            return DeltaMessage(
                tool_calls=[
                    DeltaToolCall(
                        index=0,
                        id=self.tool_id,
                        type="function",
                        function=DeltaFunctionCall(
                            name=func_name,
                        ).model_dump(exclude_none=True),
                    )
                ],
            )
        if cur_args is None:
            return None
        prev_args = self.prev_tool_call_arr[0].get("arguments_str", "")
        if not prev_args:
            delta_args = cur_args
        elif cur_args.startswith(prev_args):
            delta_args = cur_args[len(prev_args) :]
        else:
            return None
        if not delta_args:
            return None
        self.prev_tool_call_arr[0]["arguments_str"] = cur_args
        try:
            args_dict = json.loads(cur_args, strict=False)
            self.prev_tool_call_arr[0]["arguments"] = args_dict
        except json.JSONDecodeError:
            self.prev_tool_call_arr[0]["arguments"] = {}
        if len(self.streamed_args_for_tool) <= 0:
            self.streamed_args_for_tool.append("")
        self.streamed_args_for_tool[0] = cur_args
        return DeltaMessage(
            tool_calls=[
                DeltaToolCall(
                    index=0,
                    function=DeltaFunctionCall(
                        arguments=delta_args,
                    ).model_dump(exclude_none=True),
                )
            ],
        )