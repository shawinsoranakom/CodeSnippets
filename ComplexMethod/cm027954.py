async def run_agent_async(client: Anthropic, agent: Agent, query: str, history: list) -> str:
    """Run a query through a specific agent with real MCP tool connections."""
    messages = history + [{"role": "user", "content": query}]

    if not agent.mcp_servers:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=agent.system_prompt,
            messages=messages,
        )
        return response.content[0].text

    stack, tools, session_map = await connect_mcp_servers(agent)

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=agent.system_prompt,
            messages=messages,
            tools=tools,
        )

        # Agentic loop: handle tool calls until we get a final text response
        while response.stop_reason == "tool_use":
            tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
            tool_results = []

            for tool_use in tool_use_blocks:
                session = session_map.get(tool_use.name)
                if session is None:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": f"Error: Unknown tool '{tool_use.name}'",
                        "is_error": True,
                    })
                    continue

                try:
                    result = await session.call_tool(tool_use.name, tool_use.input)
                    result_text = ""
                    for content in result.content:
                        if hasattr(content, "text"):
                            result_text += content.text
                        else:
                            result_text += str(content)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": result_text,
                    })
                except Exception as e:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": f"Error calling tool: {e}",
                        "is_error": True,
                    })

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=agent.system_prompt,
                messages=messages,
                tools=tools,
            )

        # Extract final text
        text_blocks = [b.text for b in response.content if hasattr(b, "text")]
        return "\n".join(text_blocks) if text_blocks else "No response generated."

    finally:
        await stack.aclose()