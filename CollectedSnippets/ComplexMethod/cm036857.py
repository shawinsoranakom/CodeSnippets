async def test_mcp_tool_env_flag_enabled(self, client: OpenAI, model_name: str):
        response = await retry_for_tool_call(
            client,
            model=model_name,
            expected_tool_type="mcp_call",
            input=self._python_exec_input(),
            instructions=_PYTHON_TOOL_INSTRUCTION,
            tools=self._mcp_tools_payload(),
            temperature=0.0,
            extra_body={"enable_response_messages": True},
        )

        assert response.status == "completed"
        log_response_diagnostics(response, label="MCP Enabled")

        tool_call_found = False
        tool_response_found = False
        for message in response.output_messages:
            recipient = message.get("recipient")
            if recipient and recipient.startswith("python"):
                tool_call_found = True
                assert message.get("channel") == "commentary"
            parsed_message = Message.from_dict(message)
            if parsed_message.author.role == "tool" and (
                parsed_message.author.name or ""
            ).startswith("python"):
                tool_response_found = True
                assert message.get("channel") == "commentary"

        assert tool_call_found, (
            f"No Python tool call found. "
            f"Output types: "
            f"{[getattr(o, 'type', None) for o in response.output]}"
        )
        assert tool_response_found, "No Python tool response found"

        for message in response.input_messages:
            assert Message.from_dict(message).author.role != "developer"