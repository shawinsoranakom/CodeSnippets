def apply(self, **kwargs) -> SLOTS:
        content: str = kwargs.pop("content")
        thought_words = kwargs.pop("thought_words", None)
        tool_call_words = kwargs.pop("tool_call_words", None)

        def _parse_functions(json_content: str) -> list["FunctionCall"]:
            try:
                tool_calls = json.loads(json_content)
                if not isinstance(tool_calls, list):  # parallel function call
                    tool_calls = [tool_calls]

                return [FunctionCall(tc["name"], json.dumps(tc["arguments"], ensure_ascii=False)) for tc in tool_calls]
            except json.JSONDecodeError:
                raise RuntimeError(f"Invalid JSON format in function message: {str([content])}.")

        tool_call_match = None
        if tool_call_words and len(tool_call_words) == 2:
            tool_call_regex = re.compile(
                rf"{re.escape(tool_call_words[0])}(.*?){re.escape(tool_call_words[1])}", re.DOTALL
            )
            tool_call_match = re.search(tool_call_regex, content)

        if tool_call_match is None:
            thought_match = None
            if thought_words and len(thought_words) == 2:
                regex = re.compile(rf"{re.escape(thought_words[0])}(.*?){re.escape(thought_words[1])}", re.DOTALL)
                thought_match = re.search(regex, content)

            if thought_match:
                json_part = content.replace(thought_match.group(0), "")
            else:
                json_part = content

            functions = _parse_functions(json_part)
            function_str = self.tool_utils.function_formatter(functions)
            if thought_match:
                function_str = thought_match.group(0) + function_str
        else:
            thought_content = content.replace(tool_call_match.group(0), "")
            functions = _parse_functions(tool_call_match.group(1))
            function_str = self.tool_utils.function_formatter(functions)
            function_str = thought_content + function_str

        return super().apply(content=function_str)