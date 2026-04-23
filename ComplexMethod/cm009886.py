def parse(self, text: str) -> AgentAction | AgentFinish:
        # Check for tool invocation first
        tool_matches = re.findall(r"<tool>(.*?)</tool>", text, re.DOTALL)
        if tool_matches:
            if len(tool_matches) != 1:
                msg = (
                    f"Malformed tool invocation: expected exactly one <tool> block, "
                    f"but found {len(tool_matches)}."
                )
                raise ValueError(msg)
            _tool = tool_matches[0]

            # Match optional tool input
            input_matches = re.findall(
                r"<tool_input>(.*?)</tool_input>", text, re.DOTALL
            )
            if len(input_matches) > 1:
                msg = (
                    f"Malformed tool invocation: expected at most one <tool_input> "
                    f"block, but found {len(input_matches)}."
                )
                raise ValueError(msg)
            _tool_input = input_matches[0] if input_matches else ""

            # Unescape if minimal escape format is used
            if self.escape_format == "minimal":
                _tool = _unescape(_tool)
                _tool_input = _unescape(_tool_input)

            return AgentAction(tool=_tool, tool_input=_tool_input, log=text)
        # Check for final answer
        if "<final_answer>" in text and "</final_answer>" in text:
            matches = re.findall(r"<final_answer>(.*?)</final_answer>", text, re.DOTALL)
            if len(matches) != 1:
                msg = (
                    "Malformed output: expected exactly one "
                    "<final_answer>...</final_answer> block."
                )
                raise ValueError(msg)
            answer = matches[0]
            # Unescape custom delimiters in final answer
            if self.escape_format == "minimal":
                answer = _unescape(answer)
            return AgentFinish(return_values={"output": answer}, log=text)
        msg = (
            "Malformed output: expected either a tool invocation "
            "or a final answer in XML format."
        )
        raise ValueError(msg)