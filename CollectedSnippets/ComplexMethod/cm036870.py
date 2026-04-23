async def test_auto_tool_choice_first_delta_tool_call_does_not_duplicate_item(
        self, monkeypatch
    ):
        monkeypatch.setattr(envs, "VLLM_USE_EXPERIMENTAL_PARSER_CONTEXT", False)

        delta_sequence = [
            DeltaMessage(
                tool_calls=[
                    DeltaToolCall(
                        id="call_test",
                        type="function",
                        index=0,
                        function=DeltaFunctionCall(
                            name="get_weather",
                            arguments="",
                        ),
                    )
                ]
            ),
            DeltaMessage(
                tool_calls=[
                    DeltaToolCall(
                        index=0,
                        function=DeltaFunctionCall(
                            arguments='{"location":"Berlin"}',
                        ),
                    )
                ]
            ),
        ]
        events = await self._collect_events(delta_sequence)

        function_items = [
            event
            for event in events
            if event.type == "response.output_item.added"
            and getattr(event.item, "type", None) == "function_call"
        ]
        assert len(function_items) == 1
        assert function_items[0].item.name == "get_weather"

        argument_deltas = [
            event.delta
            for event in events
            if event.type == "response.function_call_arguments.delta"
        ]
        assert "".join(argument_deltas) == '{"location":"Berlin"}'