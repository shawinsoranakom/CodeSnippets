async def _run(agent: AssistantAgent, task: str, log: bool = False) -> str:
    output_stream = agent.on_messages_stream(
        [TextMessage(content=task, source="user")],
        cancellation_token=CancellationToken(),
    )
    last_txt_message = ""
    async for message in output_stream:
        if isinstance(message, ToolCallRequestEvent):
            for tool_call in message.content:
                console.print(f"  [acting]! Calling {tool_call.name}... [/acting]")

        if isinstance(message, ToolCallExecutionEvent):
            for result in message.content:
                # Compute formatted text separately to avoid backslashes in the f-string expression.
                formatted_text = result.content[:200].replace("\n", r"\n")
                console.print(f"  [observe]> {formatted_text} [/observe]")

        if isinstance(message, Response):
            if isinstance(message.chat_message, TextMessage):
                last_txt_message += message.chat_message.content
            elif isinstance(message.chat_message, ToolCallSummaryMessage):
                content = message.chat_message.content
                # only print the first 100 characters
                # console.print(Panel(content[:100] + "...", title="Tool(s) Result (showing only 100 chars)"))
                last_txt_message += content
            else:
                raise ValueError(f"Unexpected message type: {message.chat_message}")
            if log:
                print(last_txt_message)
    return last_txt_message