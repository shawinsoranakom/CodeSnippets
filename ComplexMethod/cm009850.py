def test_func_call_oldstyle(self) -> None:
        act = json.dumps([{"action_name": "foo", "action": {"__arg1": "42"}}])

        msg = AIMessage(
            content="LLM thoughts.",
            additional_kwargs={
                "function_call": {"name": "foo", "arguments": f'{{"actions": {act}}}'},
            },
        )
        result = _parse_ai_message(msg)

        assert isinstance(result, list)
        assert len(result) == 1

        action = result[0]
        assert isinstance(action, _FunctionsAgentAction)
        assert action.tool == "foo"
        assert action.tool_input == "42"
        assert action.log == (
            "\nInvoking: `foo` with `42`\nresponded: LLM thoughts.\n\n"
        )
        assert action.message_log == [msg]