def _parse_ai_message(message: BaseMessage) -> list[AgentAction] | AgentFinish:
    """Parse an AI message."""
    if not isinstance(message, AIMessage):
        msg = f"Expected an AI message got {type(message)}"
        raise TypeError(msg)

    function_call = message.additional_kwargs.get("function_call", {})

    if function_call:
        try:
            arguments = json.loads(function_call["arguments"], strict=False)
        except JSONDecodeError as e:
            msg = (
                f"Could not parse tool input: {function_call} because "
                f"the `arguments` is not valid JSON."
            )
            raise OutputParserException(msg) from e

        try:
            tools = arguments["actions"]
        except (TypeError, KeyError) as e:
            msg = (
                f"Could not parse tool input: {function_call} because "
                f"the `arguments` JSON does not contain `actions` key."
            )
            raise OutputParserException(msg) from e

        final_tools: list[AgentAction] = []
        for tool_schema in tools:
            if "action" in tool_schema:
                _tool_input = tool_schema["action"]
            else:
                # drop action_name from schema
                _tool_input = tool_schema.copy()
                del _tool_input["action_name"]
            function_name = tool_schema["action_name"]

            # A hack here:
            # The code that encodes tool input into Open AI uses a special variable
            # name called `__arg1` to handle old style tools that do not expose a
            # schema and expect a single string argument as an input.
            # We unpack the argument here if it exists.
            # Open AI does not support passing in a JSON array as an argument.
            if "__arg1" in _tool_input:
                tool_input = _tool_input["__arg1"]
            else:
                tool_input = _tool_input

            content_msg = f"responded: {message.content}\n" if message.content else "\n"
            log = f"\nInvoking: `{function_name}` with `{tool_input}`\n{content_msg}\n"
            _tool = _FunctionsAgentAction(
                tool=function_name,
                tool_input=tool_input,
                log=log,
                message_log=[message],
            )
            final_tools.append(_tool)
        return final_tools

    return AgentFinish(
        return_values={"output": message.content},
        log=str(message.content),
    )