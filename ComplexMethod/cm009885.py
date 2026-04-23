def parse_ai_message_to_tool_action(
    message: BaseMessage,
) -> list[AgentAction] | AgentFinish:
    """Parse an AI message potentially containing tool_calls."""
    if not isinstance(message, AIMessage):
        msg = f"Expected an AI message got {type(message)}"
        raise TypeError(msg)

    actions: list = []
    if message.tool_calls:
        tool_calls = message.tool_calls
    else:
        if not message.additional_kwargs.get("tool_calls"):
            return AgentFinish(
                return_values={"output": message.content},
                log=str(message.content),
            )
        # Best-effort parsing
        tool_calls = []
        for tool_call in message.additional_kwargs["tool_calls"]:
            function = tool_call["function"]
            function_name = function["name"]
            try:
                args = json.loads(function["arguments"] or "{}")
                tool_calls.append(
                    ToolCall(
                        type="tool_call",
                        name=function_name,
                        args=args,
                        id=tool_call["id"],
                    ),
                )
            except JSONDecodeError as e:
                msg = (
                    f"Could not parse tool input: {function} because "
                    f"the `arguments` is not valid JSON."
                )
                raise OutputParserException(msg) from e
    for tool_call in tool_calls:
        # A hack here:
        # The code that encodes tool input into Open AI uses a special variable
        # name called `__arg1` to handle old style tools that do not expose a
        # schema and expect a single string argument as an input.
        # We unpack the argument here if it exists.
        # Open AI does not support passing in a JSON array as an argument.
        function_name = tool_call["name"]
        _tool_input = tool_call["args"]
        tool_input = _tool_input.get("__arg1", _tool_input)

        content_msg = f"responded: {message.content}\n" if message.content else "\n"
        log = f"\nInvoking: `{function_name}` with `{tool_input}`\n{content_msg}\n"
        actions.append(
            ToolAgentAction(
                tool=function_name,
                tool_input=tool_input,
                log=log,
                message_log=[message],
                tool_call_id=tool_call["id"],
            ),
        )
    return actions